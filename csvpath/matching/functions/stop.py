from typing import Any
from csvpath.matching.functions.function import Function, ChildrenException
from csvpath.matching.productions.term import Term


class Stop(Function):
    def to_value(self, *, skip=[]) -> Any:
        return self.matches(skip=skip)

    def matches(self, *, skip=[]) -> bool:
        if self in skip:
            return False
        if self.children and len(self.children) < 2:
            ChildrenException("Stop must have 1 or 0 children")
        if self.match is None:
            self.match = True
            if len(self.children) == 1:
                b = self.children[0].matches(skip=skip)
                if b is True:
                    self.matcher.csvpath.stop()
            else:
                self.matcher.csvpath.stop()
        return self.match
