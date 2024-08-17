from typing import Any
from .function import Function
from ..productions import ChildrenException


class Percent(Function):
    def check_valid(self) -> None:
        self.validate_one_arg()
        super().check_valid()

    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()
        if self.value is None:
            which = self.children[0].to_value()
            if which not in ["scan", "match", "line"]:
                raise ChildrenException(
                    "percent() argument must be scan, match, or line"
                )
            if which == "line":
                count = self.matcher.csvpath.current_line_number()
            elif which == "scan":
                count = self.matcher.csvpath.current_scan_count()
            else:
                count = self.matcher.csvpath.current_match_count()
            total = self.matcher.csvpath.get_total_lines()
            value = count / total
            self.value = value
        return self.value

    def matches(self, *, skip=[]) -> bool:
        if self in skip:  # pragma: no cover
            return self._noop_match()
        v = self.to_value(skip=skip)
        return v is not None
