from typing import Any
from .function import Function


class Variable(Function):
    def to_value(self, *, skip=[]) -> Any:  # pragma: no cover
        self.validate_zero_args()
        return True

    def matches(self, *, skip=[]) -> bool:  # pragma: no cover
        self.validate_zero_args()
        return True
