from typing import Any
from .function import Function


class Last(Function):
    def check_valid(self) -> None:
        self.validate_zero_or_one_arg()
        super().check_valid()

    def to_value(self, *, skip=[]) -> Any:
        return self.matches(skip=skip)

    def matches(self, *, skip=[]) -> bool:
        if self.match is None:
            if not self.onmatch or self.line_matches():
                last = self.matcher.csvpath.line_monitor.is_last_line()
                last_scan = (
                    self.matcher.csvpath.scanner
                    and self.matcher.csvpath.scanner.is_last(
                        self.matcher.csvpath.line_monitor.physical_line_number
                    )
                )
                self.match = last or last_scan
                if self.match:
                    if len(self.children) == 1:
                        self.children[0].matches(skip=skip)
            else:
                self.match = False
        return self.match
