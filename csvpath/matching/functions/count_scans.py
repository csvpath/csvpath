# pylint: disable=C0114
from typing import Any
from .function import Function


class CountScans(Function):
    def check_valid(self) -> None:
        self.validate_zero_args()
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:
        if skip and self in skip:  # pragma: no cover
            return self._noop_value()
        return self.matcher.csvpath.current_scan_count
