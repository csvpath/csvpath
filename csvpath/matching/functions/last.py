from typing import Any
from .function import Function


class Last(Function):
    def to_value(self, *, skip=[]) -> Any:
        return self.matches(skip=skip)

    def matches(self, *, skip=[]) -> bool:
        if self.match is None:
            self.validate_zero_args()
            self.match = (
                self.matcher.csvpath.line_number == self.matcher.csvpath.total_lines
                or (
                    self.matcher.csvpath.scanner
                    and self.matcher.csvpath.scanner.is_last(
                        self.matcher.csvpath.line_number
                    )
                )
            )
        return self.match
