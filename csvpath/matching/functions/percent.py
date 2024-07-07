from typing import Any
from csvpath.matching.functions.function import Function, ChildrenException


class Percent(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self in skip:
            return True
        if len(self.children) != 1:
            self.matcher.print(f"Lower.to_value: must have 1 child: {self.children}")
            raise ChildrenException("Lower function must have 1 child: line|scan|match")
        which = self.children[0].to_value()

        if which not in ["scan", "match", "line"]:
            raise Exception("must be scan or match or line")

        if which == "line":
            count = self.matcher.csvpath.current_line_number()
        elif which == "scan":
            count = self.matcher.csvpath.current_scan_count()
        else:
            count = self.matcher.csvpath.current_match_count()
        total = self.matcher.csvpath.get_total_lines()
        value = count / total
        return value

    def matches(self, *, skip=[]) -> bool:
        v = self.to_value(skip=skip)
        return v is not None
