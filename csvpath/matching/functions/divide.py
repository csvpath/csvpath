from typing import Any
from .function import Function, ChildrenException
from ..productions import Equality


class Divide(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()
        if not self.value:
            self.validate_two_or_more_args()
            child = self.children[0]
            siblings = child.commas_to_list()
            ret = 0
            for i, sib in enumerate(siblings):
                v = sib.to_value(skip=skip)
                if i == 0:
                    ret = v
                else:
                    if ret == float("nan") or float(v) == 0:
                        ret = float("nan")
                    else:
                        ret = float(ret) / float(v)
            self.value = ret
        return self.value

    def matches(self, *, skip=[]) -> bool:
        return self._noop_match()  # pragma: no cover
