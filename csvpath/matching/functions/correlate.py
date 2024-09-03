# pylint: disable=C0114
from typing import Any
from .function import Function
from ..productions import ChildrenException
import pandas as pd


class Correlate(Function):
    """does a statistical correlation test on the values of two headers"""

    def check_valid(self) -> None:
        self.validate_two_args()
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:
        if skip and self in skip:  # pragma: no cover
            return self._noop_value()
        if self.value is None:
            om = self.has_onmatch()
            if not om or self.line_matches():
                child = self.children[0]
                left = child.left
                right = child.right
                leftlist = left.to_value()
                rightlist = right.to_value()
                leftlist, rightlist = self._trim(leftlist, rightlist)
                ll = pd.Series(leftlist)
                rl = pd.Series(rightlist)
                corr = ll.corr(rl)
                f = float(corr)
                f = round(f, 2)
                self.value = f
        return self.value

    def matches(self, *, skip=None) -> bool:
        self.to_value(skip=skip)
        return self._noop_match()  # pragma: no cover

    def _trim(self, leftlist, rightlist):
        n = len(leftlist) if len(leftlist) < len(rightlist) else len(rightlist)
        ll = []
        rl = []
        for i in range(0, n):
            try:
                ll.append(float(leftlist[i]))
                rl.append(float(rightlist[i]))
            except Exception:
                pass
        return ll, rl
