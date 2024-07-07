from typing import Any
from csvpath.matching.functions.function import Function, ChildrenException
from csvpath.matching.productions.equality import Equality


class Multiply(Function):
    def to_value(self, *, skip=[]) -> Any:
        if not self.value:
            if len(self.children) != 1:
                raise ChildrenException("no children. there must be 1 equality child")
            child = self.children[0]
            if not isinstance(child, Equality):
                raise ChildrenException("must be 1 equality child")

            siblings = child.commas_to_list()
            ret = 0
            for i, sib in enumerate(siblings):
                v = sib.to_value(skip=skip)
                if i == 0:
                    ret = v
                else:
                    ret = v * ret
            self.value = ret
        return self.value

    def matches(self, *, skip=[]) -> bool:
        return True
