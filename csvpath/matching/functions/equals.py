from typing import Any
from .function import Function, ChildrenException
from ..productions import Equality


class Equals(Function):
    def to_value(self, *, skip=[]) -> Any:
        if not self.value:
            if len(self.children) != 1:
                raise ChildrenException("no children. there must be 1 equality child")
            child = self.children[0]
            if not isinstance(child, Equality):
                raise ChildrenException("must be 1 equality child")

            ret = False
            left = self.children[0].left.to_value()
            right = self.children[0].right.to_value()
            if (left and not right) or (right and not left):
                ret = False
            elif left is None and right is None:
                ret = True
            elif self._is_float(left) and self._is_float(right):
                ret = float(left) == float(right)
            elif f"{left}" == f"{right}":
                ret = True
            else:
                ret = False
            self.value = ret
        return self.value

    def matches(self, *, skip=[]) -> bool:
        return True

    def _is_float(self, fs) -> bool:
        try:
            float(fs)
        except Exception:
            return False
        return True
