from typing import Any
from .function import (
    Function,
    NoChildrenException,
    ChildrenException,
)


class Length(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self in skip:
            return True
        if not self.children:
            NoChildrenException(
                "length function must have a child that produces a value"
            )
        if not len(self.children) == 1:
            ChildrenException(
                "length function must have a single child that produces a value"
            )
        val = self.children[0].to_value(skip=skip)
        ret = 0
        if val:
            ret = len(f"{val}")
        return ret

    def matches(self, *, skip=[]) -> bool:
        return self.to_value(skip=skip) > 0
