from typing import Any
from .function import Function


class CountHeaders(Function):
    def check_valid(self) -> None:
        self.validate_zero_args()
        super().check_valid()

    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return True
        if self.name == "count_headers":
            return len(self.matcher.headers)
        elif self.name == "count_headers_in_line":
            return len(self.matcher.line)
