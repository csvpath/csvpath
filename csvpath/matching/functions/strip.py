from typing import Any
from .function import Function, ChildrenException


class Strip(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()
        if len(self.children) != 1:
            raise ChildrenException("In function must have 1 child")
        if self.value is None:
            v = self.children[0].to_value()
            string = f"{v}"
            self.value = string.strip()
        return self.value

    def matches(self, *, skip=[]) -> bool:
        if self in skip:  # pragma: no cover
            return self._noop_match()
        self.to_value(skip=skip)
        return True
