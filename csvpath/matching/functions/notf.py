from typing import Any
from csvpath.matching.functions.function import (
    Function,
    NoChildrenException,
    ChildrenException,
)


class Not(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self in skip:
            return True
        if not self.children:
            NoChildrenException("Not function must have a child that produces a value")
        if not len(self.children) == 1:
            self.matcher.print(f"Not.to_value: should be 1 children: {self.children}")
            ChildrenException(
                "not function must have a single child that produces a value"
            )
        m = self.children[0].matches(skip=skip)
        self.matcher.print(f"Not.to_value: matches: {m}")
        m = not m
        return m

    def matches(self, *, skip=[]) -> bool:
        return self.to_value(skip=skip)
