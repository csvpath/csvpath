from typing import Any
from .function import Function, ChildrenException


class Above(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()
        self.validate_two_args()
        if self.value is None:
            thischild = self.children[0].children[0]
            abovethatchild = self.children[0].children[1]
            this_is = thischild.to_value(skip=skip)
            above_that = abovethatchild.to_value(skip=skip)
            this = -1
            that = -1
            try:
                this = float(this_is)
                that = float(above_that)
                self.value = this > that
            except Exception:
                # returning false because whatever the operands were they aren't above and below
                self.value = False
        return self.value

    def matches(self, *, skip=[]) -> bool:
        if self in skip:  # pragma: no cover
            return self._noop_match()
        return self.to_value(skip=skip)
