from typing import Any
from .function import Function


class No(Function):
    def to_value(self, *, skip=[]) -> Any:
        return False

    def matches(self, *, skip=[]) -> bool:
        return False
