from typing import Any
from csvpath.matching.functions.function import Function


class CountLines(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self.value is None:
            if self.matcher:
                self.value = self.matcher.csvpath.current_line_number()
        return self.value
