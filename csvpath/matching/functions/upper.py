from typing import Any
from csvpath.matching.functions.function import Function, ChildrenException


class Upper(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self in skip:
            return True
        if len(self.children) != 1:
            self.matcher.print(
                f"Upper.to_value: must have 1 equality child: {self.children}"
            )
            raise ChildrenException("Upper function must have 1 child")

        value = self.children[0].to_value(skip=skip)
        value = f"{value}".upper()
        return value

    def matches(self, *, skip=[]) -> bool:
        v = self.to_value(skip=skip)
        return v is not None
