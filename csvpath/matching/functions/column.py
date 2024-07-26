from typing import Any
from csvpath.matching.functions.function import Function, ChildrenException
from csvpath.matching.productions.term import Term


class Column(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self in skip:
            return True
        if self.children and len(self.children) != 1:
            ChildrenException("Column must have a child")
        if not isinstance(self.children[0], Term):
            ChildrenException("Column child must be a term")
        if not self.value:
            v = self.children[0].to_value()
            if isinstance(v, int) or v.isdigit():
                self.value = self.matcher.header_name(int(v))
            else:
                self.value = self.matcher.header_index(v)
        return self.value

    def matches(self, *, skip=[]) -> bool:
        return True
