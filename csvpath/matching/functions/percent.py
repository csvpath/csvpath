from typing import Any
from csvpath.matching.functions.function import Function, ChildrenException
import datetime

class Percent(Function):

    def to_value(self) -> Any:
        if len(self.children) != 1:
            self.matcher.print(f"Lower.to_value: must have 1 child: {self.children}")
            raise ChildrenException("Lower function must have 1 child: line|scan|match")
        which = self.children[0].to_value()

        if which not in ["scan", "match", "line"]:
            raise Exception("must be scan or match or line")
        if which == "line":
            value = self.matcher.csvpath.current_line_number() / self.matcher.csvpath.get_total_lines()
        elif which == "scan":
            value = self.matcher.csvpath.current_scan_count() /  self.matcher.csvpath.get_total_lines()
        else:
            value = self.matcher.csvpath.current_match_count() /  self.matcher.csvpath.get_total_lines()

        return value

    def matches(self) -> bool:
        v = self.to_value()
        return v is not None




