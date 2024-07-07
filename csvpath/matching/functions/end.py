from typing import Any
from csvpath.matching.functions.function import Function, ChildrenException


class End(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self in skip:
            return True
        if self.children and len(self.children) > 0:
            ChildrenException("end must not have a child")
        if not self.value:
            i = self.matcher.last_header_index()
            if i:
                self.value = self.matcher.line[i]
        return self.value

    def matches(self, *, skip=[]) -> bool:
        return self.to_value(skip=skip) is not None
