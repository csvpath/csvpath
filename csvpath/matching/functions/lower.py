from typing import Any
from .function import Function, ChildrenException
from ..productions import Term, Variable, Header


class Lower(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()
        self.validate_one_arg(types=[Term, Variable, Header, Function])

        value = self.children[0].to_value(skip=skip)
        value = f"{value}".lower()
        return value

    def matches(self, *, skip=[]) -> bool:
        self.to_value(skip=skip)
        return self._noop_match()
