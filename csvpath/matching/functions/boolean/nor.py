from typing import Any
from ..function_focus import MatchDecider
from csvpath.matching.productions import Matchable
from ..args import Args


class Nor(MatchDecider):
    def check_valid(self) -> None:  # pragma: no cover
        self.description = [
            self.wrap(
                f"""{self.name}() tests if its contained match components are all False.

                {self.name}() is the inverse of and(). Matching is ANDed by default. Like and()
                {self.name}() helps simplify expressions, in this case by minimizing the number
                of not() functions needed.
            """
            ),
        ]
        # self.aliases = ["nor"]
        self.args = Args(matchable=self)
        a = self.args.argset()
        a.arg(name="Eval this", types=[Matchable], actuals=[None, Any])
        a.arg(name="And eval this", types=[Matchable], actuals=[None, Any])
        self.args.validate(self.siblings_or_equality())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:  # pragma: no cover
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
        child = self.children[0]
        siblings = child.commas_to_list()
        for sib in siblings:
            if sib.matches(skip=skip):
                self.match = False
                break
        else:
            self.match = True
