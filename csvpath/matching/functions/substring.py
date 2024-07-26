from typing import Any
from csvpath.matching.functions.function import Function, ChildrenException


class Substring(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self in skip:
            return True
        if len(self.children) != 1:
            raise ChildrenException("In function must have 1 child")
        if self.children[0].op != ",":
            raise ChildrenException(
                f"Substring function must have an equality with the ',' operation, not {self.children[0].op}"
            )
        if self.value is None:
            i = self.children[0].right.to_value()
            if not isinstance(i, int):
                raise ChildrenException(
                    "Substring function must have an int righthand child"
                )
            i = int(i)
            string = self.children[0].left.to_value()
            string = f"{string}"
            if i >= len(string):
                self.value = string
            else:
                self.value = string[0:i]
        return self.value

    def matches(self, *, skip=[]) -> bool:
        v = self.to_value(skip=skip)
        return v is not None
