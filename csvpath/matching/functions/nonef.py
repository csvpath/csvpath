from typing import Any
from .function import Function


class Nonef(Function):
    def to_value(self, *, skip=[]) -> Any:  # pragma: no cover
        return None

    def matches(self, *, skip=[]) -> bool:  # pragma: no cover
        return self._noop_match()
