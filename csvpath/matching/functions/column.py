from typing import Any
from .function import Function
from ..productions import (
    Term,
    ChildrenException,
    Equality,
    DataException,
    ConfigurationException,
)


class Column(Function):
    """depreciated. the word column is confusing since
    CsvPath takes a position on the words column vs. header.
    This was one of the few places the word was used regularly.
    we also wanted the additional functionality in HeaderName
    so it is time to phase Column out.
    """

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


class HeaderName(Function):
    def check_valid(self) -> None:
        self.validate_one_or_two_args()
        super().check_valid()

    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()
        if not self.value:
            child = self.children[0]

            hname = None
            hindex = None
            v = None
            child_two = None
            if isinstance(child, Equality):
                siblings = child.commas_to_list()
                child = siblings[0]
                v = child.to_value()
                child_two = siblings[1]
            else:
                v = child.to_value()
            if isinstance(v, int) or v.isdigit():
                i = int(v)
                if i < 0:
                    hlen = len(self.matcher.csvpath.headers)
                    c = hlen + i
                    if i < 0:
                        c = c - 1
                    i = c
                hname = self.matcher.header_name(i)
            else:
                hindex = self.matcher.header_index(v)
            if child_two:
                v2 = child_two.to_value()
                if hname is None and self.name == "header_index":
                    self.value = hindex == v2
                elif hindex is None and self.name == "header_name":
                    self.value = hname == v2
                elif hname is None and hindex is None:
                    self.value = False
                else:
                    raise ConfigurationException("Unknown function name: {self.name}")
            else:
                self.value = hname if hindex is None else hindex
        return self.value

    def matches(self, *, skip=[]) -> bool:
        if self in skip:
            return self._noop_match()  # pragma: no cover
        if self.match is None:
            v = self.to_value()
            if v is None:
                self.match = False
            elif isinstance(v, int) or v.isdigit() and int(v) >= 0:
                self.match = True
            elif isinstance(v, bool):
                self.match = v
            elif isinstance(v, str):
                self.match = True
            else:
                raise DataException("Unexpected value returned: {v}.")
        return self.match
