# pylint: disable=C0114
import pandas as pd
from ..function_focus import ValueProducer


class Correlate(ValueProducer):
    """does a statistical correlation test on the values of two headers"""

    def check_valid(self) -> None:
        self.validate_two_args()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        child = self.children[0]
        left = child.left
        right = child.right
        leftlist = left.to_value(skip=skip)
        rightlist = right.to_value(skip=skip)
        leftlist, rightlist = self._trim(leftlist, rightlist)
        ll = pd.Series(leftlist)
        rl = pd.Series(rightlist)
        corr = ll.corr(rl)
        f = float(corr)
        f = round(f, 2)
        self.value = f

    def _decide_match(self, skip=None) -> None:
        self.to_value(skip=skip)
        self.match = self._noop_match()  # pragma: no cover

    def _trim(self, leftlist, rightlist):
        n = len(leftlist) if len(leftlist) < len(rightlist) else len(rightlist)
        ll = []
        rl = []
        for i in range(0, n):
            try:
                ll.append(float(leftlist[i]))
                rl.append(float(rightlist[i]))
            except (TypeError, ValueError):
                pass
        return ll, rl
