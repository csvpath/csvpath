# pylint: disable=C0114
from typing import Any
from .function import Function
from ..productions import Term, Variable, Header
from ..util.exceptions import DataException
from ..util.expression_utility import ExpressionUtility


class Round(Function):
    def check_valid(self) -> None:
        self.validate_one_or_two_args(
            left=[Term, Variable, Header, Function], right=[Term]
        )
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:
        if skip and self in skip:  # pragma: no cover
            return self._noop_value()
        if self.value is None:
            value = self._value_one()
            places = self._value_two()
            if places is None:
                places = 2
            places = ExpressionUtility.to_int(places)
            value = ExpressionUtility.to_float(value)
            if not (type(value) is float):
                de = DataException(f"Must be a float or int, not {value}")
                de.datum = value
                de.message = f"Must be a float or int, not {value}"
                raise de
            self.value = round(value, places)
        return self.value

    def matches(self, *, skip=None) -> bool:
        self.to_value(skip=skip)
        return self._noop_match()
