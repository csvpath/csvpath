from typing import Any
from csvpath.matching.functions.function import Function, ChildrenException
import datetime

class Concat(Function):

    def to_value(self) -> Any:
        if len(self.children) != 1:
            print(f"In.to_value: must have 1 equality child: {self.children}")
            raise ChildrenException("In function must have 1 child")
        if self.children[0].op != ",":
            raise ChildrenException(f"In function must have an equality with the ',' operation, not {self.children[0].op}")
        left = self.children[0].children[0]
        right = self.children[0].children[1]
        value = f"{left.to_value()}{right.to_value()}"
        return value

    def matches(self) -> bool:
        v = self.to_value()
        return v is not None




