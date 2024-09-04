# pylint: disable=C0114
from typing import Any
from .function import Function


class Divide(Function):
    """divides numbers"""

    def check_valid(self) -> None:
        self.validate_two_or_more_args()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        child = self.children[0]
        siblings = child.commas_to_list()
        ret = 0
        for i, sib in enumerate(siblings):
            v = sib.to_value(skip=skip)
            if i == 0:
                ret = v
            else:
                if ret == float("nan") or float(v) == 0:
                    ret = float("nan")
                else:
                    ret = float(ret) / float(v)
        self.value = ret

    def matches(self, *, skip=None) -> bool:
        return self._noop_match()  # pragma: no cover
