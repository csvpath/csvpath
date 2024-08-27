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
            self.matcher.csvpath.headers = self.matcher.line[:]
            self.matcher.header_dict = None
            self.matcher.csvpath.logger.warning(
                f"Resetting headers mid run! Line number: {self.matcher.csvpath.line_number}."
            )
            self.value = True
        return self.value

    def matches(self, *, skip=[]) -> bool:
        if self in skip:  # pragma: no cover
            return self._noop_match()
        return self.to_value(skip=skip)
