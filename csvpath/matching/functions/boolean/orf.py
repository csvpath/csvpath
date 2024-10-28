# pylint: disable=C0114
from typing import Any
from ..function_focus import MatchDecider
from csvpath.matching.productions import (
    Term,
    Variable,
    Header,
    Reference,
    Equality,
    Matchable,
)
from ..function import Function
from ..args import Args


class Or(MatchDecider):
    """does a logical OR of match components"""

    def __init__(self, matcher: Any, name: str, child: Matchable = None) -> None:
        super().__init__(matcher, name=name, child=child)
        self.hold = []

    def reset(self) -> None:
        self.hold = []
        super().reset()

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset()
        a.arg(types=[Matchable], actuals=[None, Any])
        a.arg(types=[Matchable], actuals=[None, Any])
        self.args.validate(self.siblings_or_equality())
        super().check_valid()

    def raise_if(self, e, *, cause=None) -> None:
        # not bubbling up until we know we don't have a
        # match on all options
        self.hold.append((e, cause))

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
        child = self.children[0]
        siblings = child.commas_to_list()
        for sib in siblings:
            b = sib.matches(skip=skip)
            if b:
                self.match = True
                # if we find a True we succeed and dump any errors
                self.hold = []
                return
        self.match = False
        # if we fail we progress any errors up the stack
        for err in self.hold:
            super().raise_if(err[0], cause=err[1])
        self.hold = []
