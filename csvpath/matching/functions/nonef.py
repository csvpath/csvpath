# pylint: disable=C0114
from typing import Any
from .function import Function


class Nonef(Function):
    def check_valid(self) -> None:
        self.validate_zero_args()
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:  # pragma: no cover
        return None

    def matches(self, *, skip=None) -> bool:  # pragma: no cover
        return self._noop_match()
