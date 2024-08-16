from typing import Any
from .function import Function


class CountLines(Function):
    def to_value(self, *, skip=[]) -> Any:
        self.validate_zero_args()
        if self.value is None:
            if self.matcher:
                self.value = self.matcher.csvpath.current_line_number()
        return self.value
