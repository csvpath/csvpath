# pylint: disable=C0114
from random import randrange
from csvpath.matching.util.exceptions import ChildrenException
from ..function_focus import ValueProducer
from csvpath.matching.productions import Term, Header, Variable
from ..function import Function
from ..args import Args


class Random(ValueProducer):
    """returns a random int within a range"""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset(2)
        a.arg(types=[Term, Variable, Header, Function], actuals=[int])
        a.arg(types=[Term, Variable, Header, Function], actuals=[int])
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        lower = self.children[0].left.to_value(skip=skip)
        upper = self.children[0].right.to_value(skip=skip)
        if lower is None:
            lower = 0
        if upper is None or upper <= lower:
            raise ChildrenException("Upper must be an int > than the first arg")
        lower = int(lower)
        upper = int(upper)
        # we are inclusive, but randrange is not
        upper += 1
        self.value = randrange(lower, upper, 1)

    def _decide_match(self, skip=None) -> None:
        self.match = self._noop_value()  # pragma: no cover
