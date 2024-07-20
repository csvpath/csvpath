from typing import Any
from csvpath.matching.functions.function import Function, ChildrenException
from csvpath.matching.productions.term import Term


class Stop(Function):
    def to_value(self, *, skip=[]) -> Any:
        return self.matches(skip=skip)

    def matches(self, *, skip=[]) -> bool:
        if self in skip:
            return False
        if self.children and len(self.children) != 1:
            ChildrenException("Stop must have a child")
        if self.match is None:
            b = self.children[0].matches(skip=skip)
            if b is True:
                self.matcher.csvpath.stop()
            self.match = (
                True  # we're always true, but we only stop if we calculated true
            )
        return self.match
