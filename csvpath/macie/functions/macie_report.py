from csvpath.matching.functions.function_focus import SideEffect
from csvpath.matching.functions.args import Args

from .macie_run import MacieRun


class MacieReport(SideEffect):
    """prints the Macie summary and stores the findings. Generated as
    last.nocontrib() -> macie_report()."""

    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                Prints one summary line per Macie identifier to the macie
                print stream and stores the findings in the macie_findings
                variable. Use it with last().

                If the run was stopped by the findings limit, the summary
                was already reported when it stopped.
            """
            ),
        ]
        self.args = Args(matchable=self)
        self.args.argset(0)
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    def override_frozen(self) -> bool:
        #
        # a file with no scanned data line, e.g. header-only, has last()
        # fire on a final, frozen pass. last() lifts the freeze only for its
        # own child, not for the right side of last() -> macie_report(),
        # so we must run when frozen, as last() and fail() do
        #
        return True

    def _decide_match(self, skip=None) -> None:
        csvpath = self.matcher.csvpath
        #
        # frozen variables can't be set. lift the freeze to store the
        # findings, restoring it after, as last() does (#324)
        #
        was_frozen = csvpath.is_frozen
        csvpath.is_frozen = False
        try:
            MacieRun.for_matcher(matcher=self.matcher).report()
        finally:
            csvpath.is_frozen = was_frozen
        self.match = self.default_match()
