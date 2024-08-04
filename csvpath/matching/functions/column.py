from typing import Any
from .function import Function, ChildrenException
from ..productions import Term


class Column(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self in skip:
            return True
        if self.children and len(self.children) != 1:
            raise ChildrenException("Column must have a child")
        if not self.value:
            v = self.children[0].to_value()
            if isinstance(v, int) or v.isdigit():
                i = int(v)
                if i < 0:
                    hlen = len(self.matcher.headers)
                    c = hlen + i
                    if i < 0:
                        c = c - 1
                    i = c
                self.value = self.matcher.header_name(i)
            else:
                self.value = self.matcher.header_index(v)
        return self.value

    def matches(self, *, skip=[]) -> bool:
        return True
