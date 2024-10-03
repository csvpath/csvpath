# pylint: disable=C0114
from ..function_focus import ValueProducer
from csvpath.matching.productions import Term, Variable, Header, Reference
from ..function import Function
from ..args import Args


class StartsWith(ValueProducer):
    """checks if a string begins with another string"""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset(2)
        a.arg(types=[Term, Variable, Header, Function, Reference], actuals=[str])
        a.arg(types=[Term, Variable, Header, Function, Reference], actuals=[str])
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        v = self.children[0].left.to_value(skip=skip)
        v = f"{v}".strip()
        sw = self.children[0].right.to_value(skip=skip)
        sw = f"{sw}".strip()
        self.value = v.startswith(sw)

    def _decide_match(self, skip=None) -> None:
        self.match = self.to_value(skip=skip)
