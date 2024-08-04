from typing import Any
from .function import Function


class Header(Function):
    def to_value(self, *, skip=[]) -> Any:
        return self.matches(skip=skip)

    def matches(self, *, skip=[]) -> bool:
        if self in skip:
            return True if self.match is None else self.match
        if self.match is None:
            if len(self.children) == 1:
                v = self.children[0].to_value()
                if isinstance(v, int) or v.isdigit():
                    i = int(v)
                    if i < 0 or i >= len(self.matcher.headers):
                        self.match = False
                    else:
                        self.match = True
                else:
                    self.match = self.matcher.header_index(v) is not None
            else:
                self.match = True
        return self.match
