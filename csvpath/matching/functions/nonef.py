from typing import Any
from .function import Function


class Nonef(Function):
    def to_value(self, *, skip=[]) -> Any:  # pragma: no cover
        self.validate_zero_args()
        return None

    def matches(self, *, skip=[]) -> bool:  # pragma: no cover
        self.validate_zero_args()
        return self._noop_match()
