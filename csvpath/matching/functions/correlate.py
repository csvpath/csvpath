from typing import Any
from .function import Function, ChildrenException
import pandas as pd


class Correlate(Function):
    def _float(self, v: Any) -> float:
        try:
            return float(v)
        except Exception:
            return None

    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()
        if len(self.children) != 1:
            raise ChildrenException("Correlate function must have 1 child")
        if self.children[0].op != ",":
            raise ChildrenException(
                f"Correlate function must have an equality with the ',' operation, not {self.children[0].op}"
            )
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

    def matches(self, *, skip=[]) -> bool:
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
