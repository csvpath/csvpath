# pylint: disable=C0114
from ..function_focus import MatchDecider
from csvpath.matching.productions import Variable, Header, Reference, Equality
from ..function import Function
from ..args import Args


class Not(MatchDecider):
    """returns the boolean inverse of a value"""

    def check_valid(self) -> None:
        # self.validate_one_arg()
        args = Args()
        a = args.argset(1)
        a.arg(types=[Variable, Header, Function, Reference, Equality], actuals=[bool])
        args.validate(self.siblings_or_equality())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
        m = self.children[0].matches(skip=skip)
        m = not m
        self.match = m
