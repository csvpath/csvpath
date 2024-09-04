# pylint: disable=C0114

from typing import Any
from .function import Function
from ..util.expression_utility import ExpressionUtility


class Add(Function):
    """this class adds numbers"""

    def check_valid(self) -> None:
        self.validate_two_or_more_args()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        child = self.children[0]
        siblings = child.commas_to_list()
        ret = 0
        for sib in siblings:
            v = sib.to_value(skip=skip)
            if ExpressionUtility.is_none(v):
                v = 0
            ret = float(v) + float(ret)
        self.value = ret

    def matches(self, *, skip=None) -> bool:
        return self._noop_match()  # pragma: no cover
