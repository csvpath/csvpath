from typing import Any
from .function import (
    Function,
    ChildrenException,
)


class Not(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self in skip:
            return True
        if not self.children:
            raise ChildrenException(
                "Not function must have a child that produces a value"
            )
        if not len(self.children) == 1:
            raise ChildrenException(
                "not function must have a single child that produces a value"
            )
        m = self.children[0].matches(skip=skip)
        m = not m
        return m

    def matches(self, *, skip=[]) -> bool:
        return self.to_value(skip=skip)
