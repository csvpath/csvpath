from typing import Any
from .function import (
    Function,
    ChildrenException,
)
from ..productions import Term, Variable, Header


class Length(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()
        self.validate_one_arg(types=[Term, Variable, Header, Function])
        val = self.children[0].to_value(skip=skip)
        ret = 0
        if val:
            ret = len(f"{val}")
        return ret

    def matches(self, *, skip=[]) -> bool:
        if self in skip:  # pragma: no cover
            return self._noop_match()

        return self.to_value(skip=skip) > 0
