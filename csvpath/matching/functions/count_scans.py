from typing import Any
from csvpath.matching.functions.function import Function


class CountScans(Function):
    def print(self, msg):
        if self.matcher:
            self.matcher.print(msg)

    def to_value(self, *, skip=[]) -> Any:
        if self in skip:
            return True
        return self.matcher.csvpath.current_scan_count()
