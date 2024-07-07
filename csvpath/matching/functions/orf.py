from typing import Any
from csvpath.matching.functions.function import Function, ChildrenException
from csvpath.matching.productions.equality import Equality


class Or(Function):
    def to_value(self, *, skip=[]) -> Any:
        return self.matches(skip=skip)

    def matches(self, *, skip=[]) -> bool:
        if self in skip:
            return True
        else:
            skip.append(self)
        if not self.value:
            if len(self.children) != 1:
                raise ChildrenException("no children. there must be 1 equality child")
            child = self.children[0]
            if not isinstance(child, Equality):
                raise ChildrenException("must be 1 equality child")

            siblings = child.commas_to_list()
            ret = False
            for i, sib in enumerate(siblings):
                if sib.matches(skip=skip):
                    ret = True
            self.value = ret
        return self.value
