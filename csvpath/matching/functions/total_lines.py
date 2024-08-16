from typing import Any
from .function import Function


class TotalLines(Function):
    def to_value(self, *, skip=[]) -> Any:
        self.validate_zero_args()
        if self.value is None:
            self.value = self.matcher.csvpath.total_lines + 1
        return self.value
