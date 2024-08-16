from typing import Any
from .function import Function, ChildrenException
from ..productions import Equality


class Or(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()
        return self.matches(skip=skip)

    def matches(self, *, skip=[]) -> bool:
        if self in skip:  # pragma: no cover
            return self._noop_match()
        else:
            skip.append(self)
        if not self.value:
            self.validate_two_or_more_args()
            child = self.children[0]
            siblings = child.commas_to_list()
            ret = False
            for i, sib in enumerate(siblings):
                if sib.matches(skip=skip):
                    ret = True
                    break
            self.value = ret
        return self.value
