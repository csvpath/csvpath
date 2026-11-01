from csvpath.matching.functions.function_focus import MatchDecider
from csvpath.matching.functions.args import Args
from csvpath.matching.productions import Term

from ..macie_exceptions import MacieException
from ..managed_identifier import ManagedIdentifier
from ..severity_levels import SeverityLevels
from .macie_run import MacieRun


class MacieMdi(MatchDecider):
    """a Macie managed data identifier, as our stand-in. Matches a line
    that has at least one occurrence in any cell. Reports each occurrence's
    location, never its value."""

    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                Applies our stand-in for a Macie managed data identifier to
                every cell of the line. Matches if the line has at least one
                occurrence.

                Arguments: the managed identifier's id, its category, the
                detector that finds candidates, the keyword mode (required,
                absent or none), keywords (separated by |), the keyword
                distance, severity levels (e.g. "1:HIGH"), and optionally a
                detail cap for this identifier. The detector's own data,
                e.g. card prefixes, comes from the managed identifier
                catalog.

                Each occurrence, up to the detail cap, is reported as an
                error and on the macie print stream. Generated from a Macie
                job's managed data identifiers.
            """
            ),
        ]
        self.args = Args(matchable=self)
        for n in [7, 8]:
            a = self.args.argset(n)
            a.arg(name="identifier id", types=[Term], actuals=[str])
            a.arg(name="category", types=[Term], actuals=[str])
            a.arg(name="detector", types=[Term], actuals=[str])
            a.arg(name="keyword mode", types=[Term], actuals=[str])
            a.arg(name="keywords", types=[Term], actuals=[str, Args.EMPTY_STRING])
            a.arg(name="keyword distance", types=[Term], actuals=[int])
            a.arg(name="severity levels", types=[Term], actuals=[str])
            if n == 8:
                a.arg(name="detail cap", types=[Term], actuals=[int])
        self.args.validate(self.siblings())
        super().check_valid()
        try:
            self.identifier = self._identifier()
        except (MacieException, ValueError, TypeError) as e:
            MacieRun.setup_failed(matcher=self.matcher, error=e)
            raise

    def _identifier(self) -> ManagedIdentifier:
        vs = [s.to_value() for s in self.siblings()]
        run = MacieRun.for_matcher(matcher=self.matcher)
        keywords = vs[4]
        identifier = ManagedIdentifier(
            name=vs[0],
            category=vs[1],
            detector=vs[2],
            keyword_mode=vs[3],
            keywords=[]
            if keywords is None or f"{keywords}".strip() == ""
            else f"{keywords}".split("|"),
            distance=int(vs[5]),
            severity=SeverityLevels.parse(text=vs[6]),
            catalog=run.catalog,
        )
        if identifier.name not in run.tally.tallies:
            run.add_identifier(
                name=identifier.name,
                severity=identifier.severity,
                max_detail=int(vs[7]) if len(vs) == 8 else None,
                category=identifier.category,
            )
        return identifier

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
        run = MacieRun.for_matcher(matcher=self.matcher)
        self.match = run.scan(source=self, identifier=self.identifier)
