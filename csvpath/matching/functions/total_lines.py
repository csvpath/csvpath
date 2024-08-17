from typing import Any
from .function import Function


class TotalLines(Function):
    def check_valid(self) -> None:
        self.validate_zero_args()
        super().check_valid()

    def to_value(self, *, skip=[]) -> Any:
        if self.value is None:
            self.value = self.matcher.csvpath.total_lines + 1
        return self.value
