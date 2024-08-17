from typing import Any
from .function import Function


class CountLines(Function):
    def check_valid(self) -> None:
        self.validate_zero_args()
        super().check_valid()

    def to_value(self, *, skip=[]) -> Any:
        if self.value is None:
            if self.matcher:
                self.value = self.matcher.csvpath.current_line_number()
        return self.value
