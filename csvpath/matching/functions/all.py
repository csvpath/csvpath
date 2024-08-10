from typing import Any
from .function import Function, ChildrenException
from ..productions import Equality


class All(Function):
    def to_value(self, *, skip=[]) -> Any:
        return self.matches(skip=skip)

    def matches(self, *, skip=[]) -> bool:
        if self in skip:
            return self._noop_match()
        if self.children and len(self.children) > 1:
            raise ChildrenException("All must have only 1 or 0 children")
        if self.match is None:
            self.match = False
            om = self.has_onmatch()
            if om and not self.line_matches():
                pass
            else:
                if len(self.children) == 0:
                    # all headers have a value
                    self.all_exist()
                if len(self.children) == 1:
                    if isinstance(self.children[0], Equality):
                        self.equality()
        return self.match

    def all_exist(self):
        if len(self.matcher.line) != len(self.matcher.headers):
            self.match = False
            return
        for h in self.matcher.line:
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
