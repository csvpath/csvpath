# pylint: disable=C0114
import math
from ..function_focus import ValueProducer
from csvpath.matching.productions import Term, Variable, Header, Reference
from ..function import Function
from ..args import Args


class Divide(ValueProducer):
    """divides numbers"""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset()
        a.arg(types=[Term, Variable, Header, Function, Reference], actuals=[int])
        a.arg(types=[Term, Variable, Header, Function, Reference], actuals=[int])
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        child = self.children[0]
        siblings = child.commas_to_list()
        ret = 0
        for i, sib in enumerate(siblings):
            v = sib.to_value(skip=skip)
            if i == 0:
                ret = v
            else:
                if math.isnan(ret) or float(v) == 0:
                    ret = float("nan")
                else:
                    ret = float(ret) / float(v)
        self.value = ret

    def _decide_match(self, skip=None) -> None:
        self.match = self.default_match()
