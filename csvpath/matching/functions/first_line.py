from typing import Any
from .function import Function, ChildrenException
import datetime


class FirstLine(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()
        return self.match(skip=skip)

    def matches(self, *, skip=[]) -> bool:
        if self in skip:
            return self._noop_match()  # pragma: no cover
        if len(self.children) > 0:
            raise ChildrenException(
                "firstline(), firstscan(), and firstmatch() do not take children"
            )
        if self.match is None:
            t = self.name
            if t == "firstmatch":
                if (
                    self.matcher.csvpath.match_count == 0 and self.line_matches()
                ):  # 1-based
                    self.match = True
                else:
                    self.match = False
            elif t == "firstscan":
                self.match = (
                    self.matcher.csvpath.scan_count == 1
                )  # 1-based, set before matcher is called.
            elif t == "firstline":
                print(f"firstline: line no: {self.matcher.csvpath.line_number}")
                self.match = (
                    self.matcher.csvpath.line_number == 0
                )  # 0-based, updated after matcher is called.
            else:
                raise ChildrenException(f"Unknown type: {t}")

        return self.match
