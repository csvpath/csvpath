# pylint: disable=C0114
from typing import Any
from .function import Function


class CountLines(Function):
    def check_valid(self) -> None:
        self.validate_zero_args()
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:
        if self.value is None:
            self.value = self.matcher.csvpath.line_monitor.data_line_count
        return self.value


class LineNumber(Function):
    def check_valid(self) -> None:
        self.validate_zero_args()
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:
        if self.value is None:
            self.value = self.matcher.csvpath.line_monitor.physical_line_number
        return self.value
