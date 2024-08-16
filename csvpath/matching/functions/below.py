from typing import Any
from .function import Function, ChildrenException


class Below(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()
        self.validate_two_args()
        thischild = self.children[0].children[0]
        belowthatchild = self.children[0].children[1]
        this_is = thischild.to_value(skip=skip)
        below_that = belowthatchild.to_value(skip=skip)
        this = -1
        that = -1
        try:
            this = float(this_is)
            that = float(below_that)
        except Exception:
            raise Exception(
                f"Below.to_value: this: {this}, a {this.__class__}, and {that}, a {that.__class__}"
            )
        b = this < that
        return b

    def matches(self, *, skip=[]) -> bool:
        if self in skip:  # pragma: no cover
            return self._noop_match()
        return self.to_value(skip=skip)
