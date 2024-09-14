# pylint: disable=C0114
import datetime
from ..function_focus import SideEffect
from csvpath.matching.productions import Term


class Replace(SideEffect):
    """replaces the value of the header with another value"""

    def check_valid(self) -> None:
        self.validate_two_args(left=[Term])
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        h = self._value_one(skip=skip)
        val = self._value_two(skip=skip)
        i = h
        if not isinstance(h, int):
            i = self.matcher.header_index(h)

        self.matcher.csvpath.logger.debug(
            "Replacing %s idenified as %s with %s", self.matcher.line[i], h, val
        )
        self.matcher.line[i] = val

        self._apply_default_value()

    def _decide_match(self, skip=None) -> None:
        self.to_value(skip=skip)
        self._apply_default_match()  # pragma: no cover
