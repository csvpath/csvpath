from typing import Any
from csvpath.matching.functions.function import Function, ChildrenException
from csvpath.matching.productions.equality import Equality


class Mod(Function):
    def to_value(self, *, skip=[]) -> Any:
        if not self.value:
            if len(self.children) != 1:
                raise ChildrenException("no children. there must be 1 equality child")
            child = self.children[0]
            if not isinstance(child, Equality):
                raise ChildrenException("must be 1 equality child")

            siblings = child.commas_to_list()
            if len(siblings) != 2:
                raise ChildrenException("must be 2 arguments to mod")
            ret = 0

            v = siblings[0].to_value(skip=skip)
            m = siblings[1].to_value(skip=skip)
            ret = float(v) % float(m)
            self.value = ret
        return self.value

    def matches(self, *, skip=[]) -> bool:
        return True
