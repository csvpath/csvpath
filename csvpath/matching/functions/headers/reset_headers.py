# pylint: disable=C0114
from ..function_focus import SideEffect
from csvpath.matching.functions.function import Function
from csvpath.util.line_counter import LineCounter
from ..args import Args


class ResetHeaders(SideEffect):
    """resets the headers to be the values in the current row, rather then the 0th row"""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        self.args.argset(1).arg(types=[None, Function], actuals=[])
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self._apply_default_value()

    def _decide_match(self, skip=None) -> None:
        hs = LineCounter.clean_headers(self.matcher.line[:])
        self.matcher.csvpath.headers = hs
        self.matcher.header_dict = None
        for key in self.matcher.csvpath.variables.keys():
            #
            # if we checked for header name mismatches it happened just once
            # and is now invalid. we need to delete the vars and let it happen
            # again.
            #
            if (
                key.endswith("_present")
                or key.endswith("_unmatched")
                or key.endswith("_duplicated")
                or key.endswith("_misordered")
            ):
                self.matcher.csvpath.logger.warning(  # pragma: no cover
                    "Deleting variable {key} as an old header name mismatch var"
                )
                del self.matcher.csvpath.variables[key]
        pln = self.matcher.csvpath.line_monitor.physical_line_number
        self.matcher.csvpath.logger.warning(
            f"Resetting headers mid run! Line number: {pln}."
        )
        if len(self.children) == 1:
            self.children[0].matches(skip=skip)
        self.match = self.default_match()
