from csvpath.matching.functions.function_focus import SideEffect
from csvpath.matching.functions.args import Args
from csvpath.matching.productions import Term

from ..macie_exceptions import MacieException
from .macie_run import MacieRun


class MacieJev(SideEffect):
    """Macie's NAME or ADDRESS identifier, which Macie finds with machine
    learning, checked by Jev from the columns' masked shapes
    (specs/macie/jev-names-addresses-design.md). Generated as

        macie_jev.nocontrib("NAME")

    for each of the two the wrapper selects. It never matches a line."""

    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                Checks a CSV file's columns for Macie's NAME or ADDRESS
                identifier with Jev, which is told only each column's
                masked shapes (each upper-case letter A, lower-case letter
                a and digit #), its header and the file's other headers.

                It runs only when config.ini [macie] review names the
                identifier. Its results are a model's judgments, not
                Macie's rules, and are kept in their own jev section of
                macie_findings. It never contributes to matching.
            """
            ),
        ]
        self.args = Args(matchable=self)
        a = self.args.argset(1)
        a.arg(name="identifier", types=[Term], actuals=[str])
        self.args.validate(self.siblings())
        super().check_valid()
        try:
            name = self.siblings()[0].to_value()
            MacieRun.for_matcher(matcher=self.matcher).add_jev(name=name)
        except (MacieException, ValueError, TypeError) as e:
            MacieRun.setup_failed(matcher=self.matcher, error=e)
            raise

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
        MacieRun.for_matcher(matcher=self.matcher).shape_line()
        self.match = self.default_match()
