# pylint: disable=C0114
from typing import Any
from .function import Function, ChildrenException
from ..productions import Equality


class Increment(Function):
    def check_valid(self) -> None:
        self.validate_two_args()
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:
        if skip and self in skip:  # pragma: no cover
            return self._noop_value()
        tv = self.children[0].right.to_value()
        if not isinstance(tv, int):
            raise ChildrenException("increment value must be a positive int")
        tv = int(tv)
        if tv <= 0:
            raise ChildrenException("increment value must be a positive int")
        if not self.value:
            varname = self.first_non_term_qualifier(self.name)
            v = self.matcher.get_variable(varname)
            if v is None:
                v = 0
            v2 = v
            m = self.children[0].left.matches(skip=[self])
            om = self.has_onmatch()
            lm = self.line_matches()
            if m:
                if om and lm:
                    v2 += 1
                elif not om:
                    v2 += 1
            r = 0
            incname = f"{varname}_increment"
            if v != v2:
                r = v2 % tv
                self.match = r == 0
                if self.match:
                    inc = v2 / tv
                    self.value = inc
                    self.matcher.set_variable(incname, value=inc)
                else:
                    inc = self.matcher.get_variable(incname)
                    if inc is None:
                        inc = 0
                    self.value = inc
                self.matcher.set_variable(varname, value=v2)
            else:
                self.match = False
                inc = self.matcher.get_variable(incname)
                if inc is None:
                    inc = 0
                self.value = inc
        return self.value

    def matches(self, *, skip=None) -> bool:
        self.to_value(skip=skip)
        return self.match
