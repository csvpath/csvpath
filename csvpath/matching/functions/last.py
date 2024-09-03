# pylint: disable=C0114
from typing import Any
from .function import Function


class Last(Function):
    """matches on the last line that will be scanned. last() will always run."""

    def check_valid(self) -> None:
        self.validate_zero_or_one_arg()
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:
        return self.matches(skip=skip)

    def matches(self, *, skip=None) -> bool:
        if skip and self in skip:  # pragma: no cover
            return True
        if self.match is None:
            last = self.matcher.csvpath.line_monitor.is_last_line()
            last_scan = (
                self.matcher.csvpath.scanner
                and self.matcher.csvpath.scanner.is_last(
                    self.matcher.csvpath.line_monitor.physical_line_number
                )
            )
            if last or last_scan:
                if not self.onmatch or self.line_matches():
                    self.match = True
                    if self.match:
                        if len(self.children) == 1:
                            self.children[0].matches(skip=[self])
                else:
                    self.match = False
            else:
                self.match = False
        return self.match
