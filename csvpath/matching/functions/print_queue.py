from typing import Any
from .function import Function


class PrintQueue(Function):
    def check_valid(self) -> None:
        self.validate_zero_args()
        super().check_valid()

    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()
        if self.value is None:
            if (
                not self.matcher.csvpath.printers
                or len(self.matcher.csvpath.printers) == 0
            ):
                self.value = 0
            else:
                self.value = self.matcher.csvpath.printers[0].lines_printed
        return self.value

    def matches(self, *, skip=[]) -> bool:
        return self._noop_match()
