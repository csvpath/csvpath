# pylint: disable=C0114
from typing import Any
from csvpath.matching.util.expression_utility import ExpressionUtility
from csvpath.matching.productions import Term, Variable, Header
from ..function_focus import ValueProducer
from ..function import Function
from ..args import Args


class Subtotal(ValueProducer):
    """returns the running sum of values aggregated by another value"""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset(2)
        a.arg(types=[Variable, Function, Header], actuals=[None, Any])
        a.arg(types=[Variable, Function, Header], actuals=[float, int])
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        t = self._value_one(skip=skip)
        c = self._value_two(skip=skip)
        varname = self.first_non_term_qualifier(self.name)
        val = self.matcher.get_variable(varname, tracking=t, set_if_none=0)
        val += ExpressionUtility.to_float(c)
        self.matcher.set_variable(varname, tracking=t, value=val)
        self.value = val

    def _decide_match(self, skip=None) -> None:
        self.to_value(skip=skip)
        self.match = self.default_match()
