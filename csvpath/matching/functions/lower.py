# pylint: disable=C0114
from typing import Any
from .function import Function
from ..productions import Term, Variable, Header


class Lower(Function):
    def check_valid(self) -> None:
        self.validate_one_arg(types=[Term, Variable, Header, Function])
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:
        if skip and self in skip:  # pragma: no cover
            return self._noop_value()

        value = self.children[0].to_value(skip=skip)
        value = f"{value}".lower()
        return value

    def matches(self, *, skip=None) -> bool:
        self.to_value(skip=skip)
        return self._noop_match()
