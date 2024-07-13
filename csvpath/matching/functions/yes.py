from typing import Any
from csvpath.matching.functions.function import Function


class Yes(Function):
    def to_value(self, *, skip=[]) -> Any:
        return True

    def matches(self, *, skip=[]) -> bool:
        return True
