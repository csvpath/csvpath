from typing import Any
from .function import Function


class Header(Function):
    def to_value(self, *, skip=[]) -> Any:
        return True

    def matches(self, *, skip=[]) -> bool:
        return True
