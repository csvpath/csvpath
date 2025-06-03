# pylint: disable=C0114
from ..function_focus import SideEffect
from csvpath.matching.functions.function import Function
from csvpath.util.line_counter import LineCounter
from ..args import Args


class ResetHeaders(SideEffect):
    """resets the headers to be the values in the current row, rather then the 0th row"""

    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                reset_headers() sets the headers to the values of the current row.

                This may change the number of headers. It may be that the
                header names are completely different after the reset.

                Resetting headers has no effect on the lines that have already been passed.

                If a function is passed as an argument it is evaluated after the
                header reset happens as a side-effect.
            """
            ),
        ]
        self.args = Args(matchable=self)
        self.args.argset(1).arg(
            name="evaluate this", types=[None, Function], actuals=[]
        )
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self._apply_default_value()

    def _decide_match(self, skip=None) -> None:
        hs = LineCounter.clean_headers(self.matcher.line[:])
        self.matcher.csvpath.headers = hs
        self.matcher.header_dict = None
        #
        # exp - fixing RuntimeError: dictionary changed size during iteration
        #
        keys = []
        for key in self.matcher.csvpath.variables.keys():
            #
            # if we checked for header name mismatches it happened just once
            # and is now invalid. we need to delete the vars and let it happen
            # again with the new headers.
            #
            if (
                key.endswith("_present")
                or key.endswith("_unmatched")
                or key.endswith("_duplicated")
                or key.endswith("_misordered")
            ):
                self.matcher.csvpath.logger.warning(  # pragma: no cover
                    f"Deleting variable {key} as an old header name mismatch var"
                )
                # del self.matcher.csvpath.variables[key]
                keys.append(key)
        for key in keys:
            del self.matcher.csvpath.variables[key]
        # end exp

        pln = self.matcher.csvpath.line_monitor.physical_line_number
        self.matcher.csvpath.logger.warning(
            f"Resetting headers mid run! Line number: {pln}."
        )
        if len(self.children) == 1:
            self.children[0].matches(skip=skip)
        self.match = self.default_match()
