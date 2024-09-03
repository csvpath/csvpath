# pylint: disable=C0114
from typing import Any
from .function import Function


class PrintQueue(Function):
    """returns the number of lines printed to the Printer instances"""

    def check_valid(self) -> None:
        self.validate_zero_args()
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:
        if skip and self in skip:  # pragma: no cover
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

    def matches(self, *, skip=None) -> bool:
        return self._noop_match()
