# pylint: disable=C0114
from typing import Any
from .function import Function


class CountHeaders(Function):
    def check_valid(self) -> None:
        self.validate_zero_args()
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:
        if skip and self in skip:  # pragma: no cover
            return True
        if self.name == "count_headers":
            ret = len(self.matcher.csvpath.headers)
            return ret
        elif self.name == "count_headers_in_line":
            return len(self.matcher.line)
