# pylint: disable=C0114
from typing import Any
from ..function_focus import MatchDecider
from ..args import Args
from ..function import Function
from csvpath.matching.productions import Header, Variable, Reference, Term


class Equals(MatchDecider):
    """tests the equality of two values. in most cases you don't
    need a function to test equality but in some cases it may
    help with clarity or a corner case that can't be handled
    better another way."""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset(2)
        a.arg(types=[Term, Variable, Header, Function, Reference], actuals=[Any])
        a.arg(types=[Term, Variable, Header, Function, Reference], actuals=[Any])
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
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
        self.match = ret

    def _is_float(self, fs) -> bool:
        try:
            float(fs)
        except (OverflowError, ValueError):
            return False
        return True
