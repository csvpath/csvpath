# pylint: disable=C0114
import math
from csvpath.matching.productions import Variable, Header
from csvpath.matching.util.expression_utility import ExpressionUtility
from ..function_focus import MatchDecider


class Exists(MatchDecider):
    """tests if a value exists"""

    def check_valid(self) -> None:
        self.validate_one_arg(types=[Variable, Header])
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
        v = self.children[0].to_value()
        ab = self.children[0].asbool
        if ab:
            v = ExpressionUtility.asbool(v)
            self.match = v
        elif v is None:
            self.match = False
        elif ExpressionUtility.isnan(v):
            self.match = False
        elif f"{v}".strip() != "":
            self.match = True
        else:
            self.match = False
