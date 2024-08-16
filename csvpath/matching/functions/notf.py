from typing import Any
from .function import (
    Function,
    ChildrenException,
)


class Not(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()
        self.validate_one_arg()
        m = self.children[0].matches(skip=skip)
        m = not m
        return m

    def matches(self, *, skip=[]) -> bool:
        if self in skip:  # pragma: no cover
            return self._noop_match()
        return self.to_value(skip=skip)
