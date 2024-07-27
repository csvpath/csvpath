from typing import Any
from .function import Function, ChildrenException
from ..productions import Header, Variable


class Exists(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self.value is None:
            self.value = self.matches(skip=skip)
        return self.value

    def matches(self, *, skip=[]) -> bool:
        if self in skip:
            return True
        if self.children and len(self.children) != 1:
            raise ChildrenException("Exists must have a header or variable child")
        if self.match is None:
            v = self.children[0].to_value()
            if not isinstance(self.children[0], Header) and not isinstance(
                self.children[0], Variable
            ):
                raise ChildrenException("Exists must have a header or variable child")
            if v is not None and v.strip() != "":
                self.match = True
            else:
                self.match = False
        return self.match
