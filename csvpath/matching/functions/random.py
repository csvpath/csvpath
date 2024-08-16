from typing import Any
from .function import Function, ChildrenException
from random import randrange


class Random(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()
        if self.value is None:
            self.validate_two_args()
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

    def matches(self, *, skip=[]) -> bool:
        return self._noop_value()  # pragma: no cover
