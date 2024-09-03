# pylint: disable=C0114
from typing import Any
from .function import Function
from ..productions import ChildrenException


class Percent(Function):
    """return the percent scanned, matched or data lines seen of
    the count of total data lines"""

    def check_valid(self) -> None:
        self.validate_one_arg()
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:
        if skip and self in skip:  # pragma: no cover
            return self._noop_value()
        if self.value is None:
            which = self.children[0].to_value()
            if which not in ["scan", "match", "line"]:
                raise ChildrenException(
                    "percent() argument must be scan, match, or line"
                )
            if which == "line":
                #
                # line_number is a pointer, not a count, so we add 1
                #
                count = self.matcher.csvpath.line_monitor.data_line_count
            elif which == "scan":
                count = self.matcher.csvpath.current_scan_count
            else:
                count = self.matcher.csvpath.current_match_count
            total = self.matcher.csvpath.line_monitor.data_end_line_count
            value = count / total
            self.value = round(value, 2)
            self.matcher.csvpath.logger.debug(
                f"Percent: val: {value}, cnt: {count}, total: {total}, rounded: {self.value}"  # pylint: disable=C0301
            )
        return self.value

    def matches(self, *, skip=None) -> bool:
        if skip and self in skip:  # pragma: no cover
            return self._noop_match()
        v = self.to_value(skip=skip)
        return v is not None
