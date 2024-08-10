from typing import Any
from .function import Function, ChildrenException


class Concat(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()
        if len(self.children) != 1:
            raise ChildrenException("In function must have 1 child")
        if self.children[0].op != ",":
            raise ChildrenException(
                f"In function must have an equality with the ',' operation, not {self.children[0].op}"
            )
        if self.value is None:
            child = self.children[0]
            siblings = child.commas_to_list()
            v = ""
            for s in siblings:
                v = f"{v}{s.to_value(skip=skip)}"
            self.value = v
        return self.value

    def matches(self, *, skip=[]) -> bool:
        self.to_value(skip=skip)  # pragma: no cover
        return self._noop_match()
