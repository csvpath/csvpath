from typing import Any
from csvpath.matching.functions.function import Function


class Nonef(Function):
    def to_value(self, *, skip=[]) -> Any:
        return None

    def matches(self, *, skip=[]) -> bool:
        return True
