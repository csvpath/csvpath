from typing import Any
from .function import Function, ChildrenException


class Above(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self in skip:
            return True
        if len(self.children) != 1:
            raise ChildrenException("Above function must have 1 child")
        if self.children[0].op != ",":
            raise ChildrenException(
                f"Above function must have an equality with the ',' operation, not {self.children[0].op}"
            )
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
            except Exception:
                raise Exception(
                    f"Above.to_value: this: {this}, a {this.__class__}, and {that}, a {that.__class__}"
                )
            self.value = this > that
        return self.value

    def matches(self, *, skip=[]) -> bool:
        if self in skip:
            return True
        return self.to_value(skip=skip)
