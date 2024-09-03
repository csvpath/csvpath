# pylint: disable=C0114
from typing import Any
from .function import Function


class Equals(Function):
    def check_valid(self) -> None:
        self.validate_two_args()
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:
        if skip and self in skip:  # pragma: no cover
            return self._noop_value()
        if not self.value:
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

    def matches(self, *, skip=None) -> bool:
        return self._noop_match()  # pragma: no cover

    def _is_float(self, fs) -> bool:
        try:
            float(fs)
        except Exception:
            return False
        return True
