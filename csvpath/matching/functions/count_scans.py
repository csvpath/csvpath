from typing import Any
from .function import Function


class CountScans(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self in skip:
            return self._noop_value()
        self.validate_zero_args()
        return self.matcher.csvpath.current_scan_count()
