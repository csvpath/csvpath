from typing import Any
from .function import Function


class No(Function):
    def to_value(self, *, skip=[]) -> Any:  # pragma: no cover
        return False

    def matches(self, *, skip=[]) -> bool:  # pragma: no cover
        return False
