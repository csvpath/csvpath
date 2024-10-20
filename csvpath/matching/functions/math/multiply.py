# pylint: disable=C0114
from ..function_focus import ValueProducer
from csvpath.matching.productions import Term, Variable, Header, Reference
from ..function import Function
from ..args import Args


class Multiply(ValueProducer):
    """multiplies numbers"""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset()
        a.arg(types=[Term, Variable, Header, Function, Reference], actuals=[float, int])
        a.arg(types=[Term, Variable, Header, Function, Reference], actuals=[float, int])
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        child = self.children[0]
        siblings = child.commas_to_list()
        ret = 0
        for i, sib in enumerate(siblings):
            v = sib.to_value(skip=skip)
            if v is None:
                ret = 0
                break
            if i == 0:
                ret = v
            else:
                ret = float(v) * float(ret)
        self.value = ret

    def _decide_match(self, skip=None) -> None:
        self.match = self.default_match()
