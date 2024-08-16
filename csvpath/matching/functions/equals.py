from typing import Any
from .function import Function, ChildrenException


class Equals(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()
        if not self.value:
            self.validate_two_args()
            child = self.children[0]
            ret = False
            left = child.left.to_value()
            right = child.right.to_value()
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
        return self._noop_match()  # pragma: no cover

    def _is_float(self, fs) -> bool:
        try:
            float(fs)
        except Exception:
            return False
        return True
