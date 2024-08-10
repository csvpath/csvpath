from typing import Any
from .function import Function, ChildrenException


class Upper(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()
        if len(self.children) != 1:
            raise ChildrenException("Upper function must have 1 child")

        value = self.children[0].to_value(skip=skip)
        value = f"{value}".upper()
        return value

    def matches(self, *, skip=[]) -> bool:
        if self in skip:  # pragma: no cover
            return self._noop_match()
        v = self.to_value(skip=skip)
        return v is not None
