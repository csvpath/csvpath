# pylint: disable=C0114

from typing import Any
from ..function_focus import MatchDecider
from csvpath.matching.productions import Term, Variable, Header, Reference, Equality
from ..function import Function
from ..args import Args


class And(MatchDecider):
    """ANDs match components. remember that csvpath is
    AND by default; however, there are times when you
    need more control."""

    def check_valid(self) -> None:  # pragma: no cover
        self.args = Args(matchable=self)
        a = self.args.argset()
        a.arg(
            types=[Term, Variable, Header, Function, Reference, Equality], actuals=[Any]
        )
        a.arg(
            types=[Term, Variable, Header, Function, Reference, Equality], actuals=[Any]
        )
        self.args.validate(self.siblings_or_equality())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:  # pragma: no cover
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
        child = self.children[0]
        siblings = child.commas_to_list()
        for sib in siblings:
            self.match = sib.matches(skip=skip)
            if not self.match:
                break
