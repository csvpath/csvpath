from typing import Any
from .function import Function
from ..productions import Equality


class All(Function):
    def check_valid(self) -> None:
        self.validate_zero_or_more_than_one_arg()
        super().check_valid()

    def to_value(self, *, skip=[]) -> Any:
        return self.matches(skip=skip)  # pragma: no cover

    def matches(self, *, skip=[]) -> bool:
        if self in skip:  # pragma: no cover
            return self._noop_match()
        if self.match is None:
            self.match = False
            om = self.has_onmatch()
            if om and not self.line_matches():
                pass
            else:
                cs = len(self.children)
                if cs == 0:
                    # all headers have a value
                    self.all_exist()
                if len(self.children) == 1:
                    # a list of headers have values
                    if isinstance(self.children[0], Equality):
                        self.equality()
        return self.match

    def all_exist(self):
        if len(self.matcher.line) != len(
            self.matcher.csvpath.headers
        ):  # changed to csvpath.headers
            self.match = False
            return
        for i, h in enumerate(self.matcher.line):
            if h is None or f"{h}".strip() == "":
                self.match = False
                return
        self.match = True

    def equality(self):
        siblings = self.children[0].commas_to_list()
        for s in siblings:
            v = s.to_value(skip=[self])
            if v is None or f"{v}".strip() == "":
                self.match = False
                return
        self.match = True
