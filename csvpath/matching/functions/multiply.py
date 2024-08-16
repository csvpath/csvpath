from typing import Any
from .function import Function, ChildrenException
from ..productions import Equality


class Multiply(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()
        if not self.value:
            self.validate_two_or_more_args()
            child = self.children[0]
            siblings = child.commas_to_list()
            ret = 0
            for i, sib in enumerate(siblings):
                #
                # TODO
                #
                v = sib.to_value(skip=skip)
                if i == 0:
                    ret = v
                else:
                    ret = float(v) * float(ret)
            self.value = ret
        return self.value

    def matches(self, *, skip=[]) -> bool:
        return self._noop_match()  # pragma: no cover
