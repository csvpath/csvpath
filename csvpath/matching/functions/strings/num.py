# pylint: disable=C0114
from csvpath.matching.productions import Term, Variable, Header
from csvpath.matching.util.expression_utility import ExpressionUtility
from ..function_focus import ValueProducer
from ..function import Function


class Num(ValueProducer):
    """parses a string to a number, if possible"""

    def check_valid(self) -> None:
        self.validate_one_arg(types=[Term, Variable, Header, Function])
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        value = self.children[0].to_value(skip=skip)
        if value is None:
            self.value = 0
        elif isinstance(value, int):
            self.value = value
        elif isinstance(value, float):
            self.value = value
        else:
            self.value = ExpressionUtility.to_float(value)

    def _decide_match(self, skip=None) -> None:
        self.to_value(skip=skip)
        self.match = self._noop_match()
