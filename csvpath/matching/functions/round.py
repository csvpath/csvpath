# pylint: disable=C0114
from .function import Function
from ..productions import Term, Variable, Header
from ..util.expression_utility import ExpressionUtility


class Round(Function):
    """rounds a number to a certain number of places"""

    def check_valid(self) -> None:
        self.validate_one_or_two_args(
            left=[Term, Variable, Header, Function], right=[Term]
        )
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        value = self._value_one(skip=skip)
        places = self._value_two(skip=skip)
        if places is None:
            places = 2
        places = ExpressionUtility.to_int(places)
        value = ExpressionUtility.to_float(value)
        self.value = round(value, places)

    def matches(self, *, skip=None) -> bool:
        self.to_value(skip=skip)
        return self._noop_match()
