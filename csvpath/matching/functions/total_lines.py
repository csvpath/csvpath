from typing import Any
from .function import Function


class TotalLines(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self.value is None:
            if self.matcher:
                self.value = self.matcher.csvpath.total_lines + 1
        return self.value
