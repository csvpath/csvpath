# pylint: disable=C0114
from csvpath.matching.productions import Term, Variable, Header
from csvpath.matching.util.expression_utility import ExpressionUtility
from ..function_focus import ValueProducer
from ..function import Function
from ..args import Args


class Round(ValueProducer):
    """rounds a number to a certain number of places"""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset(2)
        a.arg(
            types=[Term, Variable, Header, Function],
            actuals=[None, bool, str, float, int],
        )
        a.arg(types=[None, Term], actuals=[int])
        self.args.validate(self.siblings_or_equality())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        value = self._value_one(skip=skip)
        places = self._value_two(skip=skip)
        if places is None:
            places = 2
        places = ExpressionUtility.to_int(places)
        value = ExpressionUtility.to_float(value)
        self.value = round(value, places)

    def _decide_match(self, skip=None) -> None:
        self.to_value(skip=skip)
        self.match = self.default_match()
