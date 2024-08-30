from typing import Any
from .function import Function
from .header import Header
from .variable import Variable
from ..productions import Equality
from csvpath import ConfigurationException


class All(Function):
    def check_valid(self) -> None:
        self.validate_zero_or_more_args([Equality, Header, Variable])
        super().check_valid()

    def to_value(self, *, skip=[]) -> Any:
        return self.matches(skip=skip)  # pragma: no cover

    def matches(self, *, skip=[]) -> bool:
        if self in skip:  # pragma: no cover
            return self._noop_match()
        if self.match is None:
            om = self.has_onmatch()
            if not om or self.line_matches():
                self.match = False
                cs = len(self.children)
                if cs == 0:
                    # all headers have a value
                    self.all_exist()
                if len(self.children) == 1:
                    child = self.children[0]
                    # a list of headers have values
                    if isinstance(child, Equality):
                        self.equality()
                    elif isinstance(child, Header):
                        self.all_exist()
                    elif isinstance(child, Variable):
                        self.all_variables()
                    else:
                        raise ConfigurationException("Child cannot be {child}")
        return self.match

    def all_variables(self) -> None:
        # default is True in case no vars
        self.match = True
        for k, v in self.matcher.csvpath.variables.items():
            if v is None or f"{v}".strip() == "":
                self.match = False
                return

    def all_exist(self):
        if len(self.matcher.line) != len(self.matcher.csvpath.headers):
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
