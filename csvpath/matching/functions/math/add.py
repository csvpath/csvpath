# pylint: disable=C0114

from csvpath.matching.util.expression_utility import ExpressionUtility
from ..function_focus import ValueProducer
from csvpath.matching.productions import Term, Variable, Header, Reference
from ..function import Function
from ..args import Args


class Add(ValueProducer):
    """this class adds numbers"""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset()
        a.arg(
            types=[Term, Variable, Header, Function, Reference],
            actuals=[None, int, float],
        )
        a.arg(
            types=[Term, Variable, Header, Function, Reference],
            actuals=[None, int, float],
        )
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        child = self.children[0]
        siblings = child.commas_to_list()
        ret = 0
        for sib in siblings:
            v = sib.to_value(skip=skip)
            if ExpressionUtility.is_none(v):
                v = 0
            ret = float(v) + float(ret)
        self.value = ret

    def _decide_match(self, skip=None) -> None:
        self.match = self.default_match()
