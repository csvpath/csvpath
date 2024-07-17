from typing import Any
from csvpath.matching.functions.function import Function, ChildrenException
from csvpath.matching.productions.equality import Equality


class Increment(Function):
    def line_matches(self):
        es = self.matcher.expressions
        for e in es:
            if not e[0].matches(skip=[self]):
                return False
        return True

    def to_value(self, *, skip=[]) -> Any:
        if self in skip:
            return True
        if self.children and len(self.children) == 1:
            ChildrenException("must have a child")
        if not isinstance(self.children[0], Equality):
            ChildrenException("child must be an Equality")
        tv = self.children[0].right.to_value()
        if not isinstance(tv, int) or tv <= 0:
            ChildrenException("increment value must be a positive int")
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
            incname = f"{varname}.increment"
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

    def matches(self, *, skip=[]) -> bool:
        self.to_value(skip=skip)
        return self.match
