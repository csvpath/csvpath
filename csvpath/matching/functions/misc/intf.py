# pylint: disable=C0114
from csvpath.matching.util.expression_utility import ExpressionUtility
from ..function_focus import ValueProducer


class Int(ValueProducer):
    """attempts to convert a value to an int"""

    def check_valid(self) -> None:
        self.validate_one_arg()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        child = self.children[0]
        i = child.to_value(skip=skip)
        i = ExpressionUtility.to_int(i)
        self.value = i

    def _decide_match(self, skip=None) -> None:
        self.match = self._noop_match()  # pragma: no cover
