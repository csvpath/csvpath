# pylint: disable=C0114
from typing import Any
from .function import Function
from random import randrange


class Random(Function):
    """returns a random int within a range"""

    def check_valid(self) -> None:
        self.validate_two_args()
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:
        if skip and self in skip:  # pragma: no cover
            return self._noop_value()
        if self.value is None:
            lower = self.children[0].left.to_value()
            upper = self.children[0].right.to_value()
            if lower is None:
                lower == 0
            if upper is None or upper <= lower:
                upper == 1
            try:
                lower = int(lower)
                upper = int(upper)
                # we are inclusive, but randrange is not
                upper += 1
                self.value = randrange(lower, upper, 1)
            except Exception:
                pass
        return self.value

    def matches(self, *, skip=None) -> bool:
        return self._noop_value()  # pragma: no cover
