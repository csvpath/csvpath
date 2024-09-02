from typing import Any
from .function import Function

#
# deprecated for existence testing specific headers.
# use HeaderName instead.
#


class Header(Function):
    def check_valid(self) -> None:
        self.validate_zero_or_one_arg()
        super().check_valid()

    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()
        return self.matches(skip=skip)

    def matches(self, *, skip=[]) -> bool:
        if self in skip:  # pragma: no cover
            return self._noop_match()
        if self.match is None:
            if len(self.children) == 1:
                v = self.children[0].to_value()
                if isinstance(v, int) or v.isdigit():
                    i = int(v)
                    if i < 0 or i >= len(self.matcher.csvpath.headers):
                        self.match = False
                    else:
                        self.match = True
                else:
                    self.match = self.matcher.header_index(v) is not None
            else:
                self.match = True
        return self.match
