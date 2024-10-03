# pylint: disable=C0114
from ..function_focus import MatchDecider
from csvpath.matching.productions import Term, Variable, Header, Reference, Equality
from ..function import Function
from ..args import Args


class Or(MatchDecider):
    """does a logical OR of match components"""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset()
        a.arg(
            types=[Term, Variable, Header, Function, Reference, Equality], actuals=[int]
        )
        a.arg(
            types=[Term, Variable, Header, Function, Reference, Equality], actuals=[int]
        )
        self.args.validate(self.siblings_or_equality())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
        child = self.children[0]
        siblings = child.commas_to_list()
        ret = False
        for sib in siblings:
            if sib.matches(skip=skip):
                ret = True
                break
        self.match = ret
