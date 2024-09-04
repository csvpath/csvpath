# pylint: disable=C0114
from typing import Any
from .function import Function
from ..productions import Term, Variable, Header


class Lower(Function):
    """lowercases a string"""

    def check_valid(self) -> None:
        self.validate_one_arg(types=[Term, Variable, Header, Function])
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        value = self.children[0].to_value(skip=skip)
        self.value = f"{value}".lower()

    def matches(self, *, skip=None) -> bool:
        self.to_value(skip=skip)
        return self._noop_match()
