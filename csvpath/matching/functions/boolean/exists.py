# pylint: disable=C0114
import math
from typing import Any
from csvpath.matching.productions import Variable, Header, Reference
from csvpath.matching.util.expression_utility import ExpressionUtility
from ..function_focus import MatchDecider
from ..function import Function
from ..args import Args


class Exists(MatchDecider):
    """tests if a value exists"""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset(1)
        a.arg(types=[Variable, Header, Function, Reference], actuals=[None, Any])
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
        v = self.children[0].to_value()
        v = not ExpressionUtility.is_empty(v)
        self.match = v
