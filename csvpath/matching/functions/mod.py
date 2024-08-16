from typing import Any
from .function import Function, ChildrenException
from ..productions import Equality


class Mod(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()
        if not self.value:
            self.validate_two_args()
            child = self.children[0]
            siblings = child.commas_to_list()
            ret = 0
            try:
                v = siblings[0].to_value(skip=skip)
                m = siblings[1].to_value(skip=skip)
                ret = float(v) % float(m)
            except Exception:
                raise ChildrenException(
                    "mod()'s arguments must be convertable to float"
                )
            ret = round(ret, 2)
            self.value = ret
        return self.value

    def matches(self, *, skip=[]) -> bool:
        return self._noop_match()  # pragma: no cover
