from typing import Any
from .function import Function
from ..productions import ChildrenException


class ResetHeaders(Function):
    def check_valid(self) -> None:
        self.validate_zero_args()
        super().check_valid()

    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()
        if self.value is None:
            self.matcher.headers = self.matcher.line[:]
            self.matcher.header_dict = None
            self.matcher.logger.warning(
                f"Resetting headers mid run! Line number: {self.matcher.csvpath.line_number}."
            )
        return self.value

    def matches(self, *, skip=[]) -> bool:
        if self in skip:  # pragma: no cover
            return self._noop_match()
        return self.to_value(skip=skip)
