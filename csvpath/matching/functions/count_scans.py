from typing import Any
from .function import Function


class CountScans(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self in skip:
            return True
        return self.matcher.csvpath.current_scan_count()
