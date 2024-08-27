from typing import Any
from .function import Function
from ..productions import Term, ChildrenException


class Column(Function):
    def check_valid(self) -> None:
        self.validate_one_arg()
        super().check_valid()

    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()
        if not self.value:
            v = self.children[0].to_value()
            if isinstance(v, int) or v.isdigit():
                i = int(v)
                if i < 0:
                    hlen = len(self.matcher.csvpath.headers)
                    c = hlen + i
                    if i < 0:
                        c = c - 1
                    i = c
                self.value = self.matcher.header_name(i)
            else:
                self.value = self.matcher.header_index(v)
        return self.value

    def matches(self, *, skip=[]) -> bool:
        return self._noop_match()  # pragma: no cover
