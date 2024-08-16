from typing import Any
from .function import Function


class CountHeaders(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return True
        self.validate_zero_args()
        return len(self.matcher.headers)
