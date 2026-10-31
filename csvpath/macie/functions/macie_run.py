import logging
import weakref

from ..allow_list_set import AllowListSet
from ..arn_utility import ArnUtility as arut
from ..findings_tally import FindingsTally, IdentifierTally


class MacieRun:
    """the state the Macie functions of one csvpath share during one run:
    the allow lists, the findings tally, and the outputs. There is one per
    Matcher, so each run starts fresh. Outputs go:

    - one error per detailed occurrence, to the csvpath's error manager
    - the same line, and the summary, to the "macie" print stream
    - the findings, to the macie_findings variable (vars.json)

    Limits come from the csvpath's metadata (written by the transpiler),
    then config.ini [macie], then the defaults."""

    PRINTER = "macie"
    VARIABLE = "macie_findings"
    MAX_FINDINGS = 10000
    MAX_DETAIL = 15
    #
    # Matcher -> MacieRun. weak, so a finished run's state goes with its
    # Matcher.
    #
    _RUNS = weakref.WeakKeyDictionary()

    def __init__(self, *, matcher) -> None:
        if matcher is None or matcher.csvpath is None:
            raise ValueError("matcher and matcher.csvpath must not be None")
        self.matcher = matcher
        self.allow_lists = AllowListSet()
        self.tally = FindingsTally(
            max_findings=self._limit(
                key="max-findings", default=self.MAX_FINDINGS, minimum=1
            ),
            max_detail=self._limit(
                key="max-detail", default=self.MAX_DETAIL, minimum=0
            ),
            source_arn=self._source_arn(),
        )
        self.reported = False

    @classmethod
    def logger(cls) -> logging.Logger:
        return logging.getLogger(cls.__name__)

    @classmethod
    def for_matcher(cls, *, matcher) -> "MacieRun":
        if matcher is None:
            raise ValueError("matcher must not be None")
        run = cls._RUNS.get(matcher)
        if run is None:
            run = MacieRun(matcher=matcher)
            cls._RUNS[matcher] = run
        return run

    @classmethod
    def setup_failed(cls, *, matcher, error: Exception) -> None:
        """a Macie function could not be set up, e.g. a bad regex or limit.
        With no-raise the Framework only records the error, and the run
        would look like a clean file with no findings. So we also fail the
        run, stop it, and say so on the macie stream. The caller re-raises."""
        cls.logger().exception("Macie function setup failed: %s", error)
        csvpath = matcher.csvpath
        csvpath.is_valid = False
        csvpath.stop()
        csvpath.print_to(cls.PRINTER, f"macie: cannot run: {error}")

    def add_identifier(
        self,
        *,
        name: str,
        severity,
        max_detail: int | None = None,
        arn: str | None = None,
        category: str | None = None,
    ) -> None:
        self.tally.add(
            tally=IdentifierTally(
                name=name,
                severity=severity,
                max_detail=self.tally.max_detail if max_detail is None else max_detail,
                arn=arn,
                category=category,
            )
        )

    def record(
        self, *, source, name: str, line: int, column: int, column_name: str
    ) -> None:
        """records one occurrence at a 0-based line and 1-based column. Trips
        the breaker, and stops the csvpath, when the total reaches the
        maximum. Callers must not record once tripped."""
        detail = self.tally.record(
            name=name, row=line + 1, column=column, column_name=column_name
        )
        if detail:
            msg = FindingsTally.detail_message(
                name=name,
                occurrence=self.tally.tallies[name].count,
                line=line,
                column=column,
                column_name=column_name,
            )
            csvpath = self.matcher.csvpath
            csvpath.error_manager.handle_error(source=source, msg=msg)
            csvpath.print_to(self.PRINTER, msg)
        if self.tally.tripped:
            self.tally.stopped_at_line = line
            self.matcher.csvpath.logger.warning(
                "Macie breaker tripped at line %s after %s occurrences",
                line,
                self.tally.total,
            )
            #
            # stop() ends the run before last(), so macie_report() would
            # never run. we report here instead.
            #
            self.report()
            self.matcher.csvpath.stop()

    def report(self) -> None:
        """prints the summary and stores the findings in the macie_findings
        variable, once. last() lifts the final pass's variable freeze for
        its child (#324), so macie_report() can always store them."""
        if self.reported:
            return
        self.reported = True
        for msg in self.tally.summary_messages():
            self.matcher.csvpath.print_to(self.PRINTER, msg)
        self.matcher.csvpath.set_variable(self.VARIABLE, value=self.tally.to_findings())

    def _source_arn(self) -> str | None:
        #
        # written by the transpiler with "|" for ":" (see ArnUtility)
        #
        metadata = self.matcher.csvpath.metadata
        v = metadata.get("macie-source-arn") if metadata else None
        if v is None or f"{v}".strip() == "":
            return None
        return arut.from_metadata(value=f"{v}".strip())

    def _limit(self, *, key: str, default: int, minimum: int) -> int:
        csvpath = self.matcher.csvpath
        source = f"metadata macie-{key}"
        v = csvpath.metadata.get(f"macie-{key}") if csvpath.metadata else None
        if v is None and csvpath.config is not None:
            source = f"config.ini [macie] {key.replace('-', '_')}"
            v = csvpath.config.get(
                section="macie", name=key.replace("-", "_"), default=None
            )
        if v is None:
            return default
        try:
            i = int(f"{v}".strip())
        except ValueError as e:
            self.logger().exception("Bad %s: %r", source, v)
            raise ValueError(f"{source} must be an int, not {v!r}") from e
        if i < minimum:
            raise ValueError(f"{source} must be at least {minimum}, not {i}")
        return i
