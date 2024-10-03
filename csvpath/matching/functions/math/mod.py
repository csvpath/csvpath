# pylint: disable=C0114
from ..function_focus import ValueProducer
from csvpath.matching.productions import Term, Header, Variable, Reference
from ..function import Function
from ..args import Args


class Mod(ValueProducer):
    """takes the modulus of numbers"""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset(2)
        a.arg(types=[Term, Variable, Header, Function, Reference], actuals=[int, float])
        a.arg(types=[Term, Variable, Header, Function, Reference], actuals=[int, float])
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        child = self.children[0]
        siblings = child.commas_to_list()
        ret = 0
        v = siblings[0].to_value(skip=skip)
        m = siblings[1].to_value(skip=skip)
        ret = float(v) % float(m)
        ret = round(ret, 2)
        self.value = ret

    def _decide_match(self, skip=None) -> None:
        self.to_value(skip=skip)
        self.match = self.default_match()
