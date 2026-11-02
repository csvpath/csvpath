from csvpath.matching.functions.function_focus import MatchDecider
from csvpath.matching.functions.args import Args
from csvpath.matching.productions import Term

from ..arn_utility import ArnUtility as arut
from ..custom_identifier import CustomIdentifier
from ..macie_exceptions import MacieException
from ..severity_levels import SeverityLevels
from .macie_run import MacieRun


class MacieCdi(MatchDecider):
    """a Macie custom data identifier. Matches a line that has at least one
    occurrence in any cell. Reports each occurrence's location, never its
    value."""

    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                Applies a Macie custom data identifier to every cell of the
                line. Matches if the line has at least one occurrence.

                Arguments: name, ARN (or "" if none), regex, keywords and
                ignore words (each separated by |), maximum match distance,
                severity levels (e.g. "1:LOW 5:MEDIUM 10:HIGH"), and
                optionally a detail cap for this identifier.

                Each occurrence, up to the detail cap, is reported as an
                error and on the macie print stream. Generated from a Macie
                custom data identifier.
            """
            ),
        ]
        self.args = Args(matchable=self)
        for n in [7, 8]:
            a = self.args.argset(n)
            a.arg(name="identifier name", types=[Term], actuals=[str])
            a.arg(name="arn", types=[Term], actuals=[str, Args.EMPTY_STRING])
            a.arg(name="regex", types=[Term], actuals=[str])
            a.arg(name="keywords", types=[Term], actuals=[str, Args.EMPTY_STRING])
            a.arg(name="ignore words", types=[Term], actuals=[str, Args.EMPTY_STRING])
            a.arg(name="maximum match distance", types=[Term], actuals=[int])
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

    def _identifier(self) -> CustomIdentifier:
        vs = [s.to_value() for s in self.siblings()]
        name, arn, regex = vs[0], vs[1], vs[2]
        arn = None if arn is None or f"{arn}".strip() == "" else arut.check(arn=arn)
        if regex.startswith("/") and regex.endswith("/") and len(regex) > 1:
            regex = regex[1:-1]
        identifier = CustomIdentifier(
            name=name,
            pattern=regex,
            keywords=self._entries(text=vs[3]),
            ignore_words=self._entries(text=vs[4]),
            distance=int(vs[5]),
            severity=SeverityLevels.parse(text=vs[6]),
        )
        run = MacieRun.for_matcher(matcher=self.matcher)
        if identifier.name not in run.tally.tallies:
            run.add_identifier(
                name=identifier.name,
                severity=identifier.severity,
                max_detail=int(vs[7]) if len(vs) == 8 else None,
                arn=arn,
            )
        return identifier

    @classmethod
    def _entries(cls, *, text) -> list[str]:
        if text is None or f"{text}".strip() == "":
            return []
        return f"{text}".split("|")

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
        run = MacieRun.for_matcher(matcher=self.matcher)
        self.match = run.scan(source=self, identifier=self.identifier)
