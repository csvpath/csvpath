from typing import Any
from csvpath.matching.functions.function import (
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
            self.matcher.print(
                f"Length.to_value: should be 1 children: {self.children}"
            )
            ChildrenException(
                "length function must have a single child that produces a value"
            )
        val = self.children[0].to_value(skip=skip)
        self.matcher.print(f"Length.to_value: val: {val}")
        ret = 0
        if val:
            ret = len(f"{val}")
        self.matcher.print(f"Length.to_value: val: {val}")
        return ret

    def matches(self, *, skip=[]) -> bool:
        return self.to_value(skip=skip) > 0
