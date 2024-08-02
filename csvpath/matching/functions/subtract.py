from typing import Any
from .function import Function, ChildrenException
from ..productions import Equality, Term


class Subtract(Function):
    def to_value(self, *, skip=[]) -> Any:
        if not self.value:
            if len(self.children) != 1:
                raise ChildrenException("no children. there must be 1 child")
            child = self.children[0]
            if isinstance(child, Term):
                v = child.to_value()
                v = int(v)
                self.value = v * -1
            elif isinstance(child, Equality):
                siblings = child.commas_to_list()
                ret = 0
                for i, sib in enumerate(siblings):
                    v = sib.to_value(skip=skip)
                    if i == 0:
                        ret = v
                    else:
                        ret = float(ret) - float(v)
                self.value = ret
            else:
                raise ChildrenException(
                    f"must be 1 child, either equality or a term containing an int, not {child}"
                )
        return self.value

    def matches(self, *, skip=[]) -> bool:
        return True
