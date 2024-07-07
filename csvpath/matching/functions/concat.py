from typing import Any
from csvpath.matching.functions.function import Function, ChildrenException


class Concat(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self in skip:
            return True
        if len(self.children) != 1:
            self.matcher.print(
                f"In.to_value: must have 1 equality child: {self.children}"
            )
            raise ChildrenException("In function must have 1 child")
        if self.children[0].op != ",":
            raise ChildrenException(
                f"In function must have an equality with the ',' operation, not {self.children[0].op}"
            )
        left = self.children[0].children[0]
        right = self.children[0].children[1]
        value = f"{left.to_value(skip=skip)}{right.to_value(skip=skip)}"
        return value

    def matches(self, *, skip=[]) -> bool:
        v = self.to_value(skip=skip)
        return v is not None
