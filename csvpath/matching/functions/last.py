from typing import Any
from .function import Function


class Last(Function):
    def to_value(self, *, skip=[]) -> Any:
        return self.matches(skip=skip)

    def matches(self, *, skip=[]) -> bool:
        if self.match is None:
            self.match = (
                self.matcher.csvpath.line_number == self.matcher.csvpath.total_lines
            )
        return self.match
