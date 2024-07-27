from typing import Any
from .function import Function


class Variable(Function):
    def to_value(self, *, skip=[]) -> Any:
        return True

    def matches(self, *, skip=[]) -> bool:
        return True
