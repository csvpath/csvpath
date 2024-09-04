# pylint: disable=C0114
from .function import Function
from ..util.expression_utility import ExpressionUtility


class Int(Function):
    """attempts to convert a value to an int"""

    def check_valid(self) -> None:
        self.validate_one_arg()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        child = self.children[0]
        i = child.to_value(skip=skip)
        i = ExpressionUtility.to_int(i)
        self.value = i

    def matches(self, *, skip=None) -> bool:
        return self._noop_match()  # pragma: no cover
