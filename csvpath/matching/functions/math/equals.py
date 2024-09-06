# pylint: disable=C0114
from ..function_focus import MatchDecider


class Equals(MatchDecider):
    """tests the equality of two values"""

    def check_valid(self) -> None:
        self.validate_two_args()
        super().check_valid()

    def _decide_match(self, skip=None) -> None:
        self.match = self._noop_match()

    def _produce_value(self, skip=None) -> None:
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

    def _is_float(self, fs) -> bool:
        try:
            float(fs)
        except (OverflowError, ValueError):
            return False
        return True
