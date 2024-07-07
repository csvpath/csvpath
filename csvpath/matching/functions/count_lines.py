from typing import Any
from csvpath.matching.functions.function import Function


class CountLines(Function):
    def print(self, msg):
        if self.matcher:
            self.matcher.print(msg)

    def to_value(self, *, skip=[]) -> Any:
        if self.matcher:
            return self.matcher.csvpath.current_line_number()
