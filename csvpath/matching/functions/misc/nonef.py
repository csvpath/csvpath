# pylint: disable=C0114
from typing import Any
from ..function_focus import ValueProducer
from csvpath.matching.util.expression_utility import ExpressionUtility
from csvpath.matching.productions import Variable, Header, Reference
from csvpath.matching.functions.function import Function
from ..args import Args


class Nonef(ValueProducer):
    """returns None"""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        self.args.argset(0)
        a = self.args.argset(1)
        a.arg(types=[Variable, Header, Function, Reference], actuals=[None, Any])
        self.args.validate(self.siblings())
        super().check_valid()

    # def to_value(self, *, skip=None) -> Any:  # pragma: no cover
    def _produce_value(self, skip=None) -> None:
        self.value = None

    def _decide_match(self, *, skip=None) -> None:  # pragma: no cover
        if len(self.children) == 0:
            self.match = True
        else:
            self.match = ExpressionUtility.is_none(self._value_one(skip=skip))
