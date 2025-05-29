# pylint: disable=C0114

from typing import Any
from ..function_focus import MatchDecider
from csvpath.matching.productions import Matchable
from ..function import Function
from ..args import Args


class And(MatchDecider):
    """ANDs match components. remember that csvpath is
    AND by default; however, there are times when you
    need more control."""

    def check_valid(self) -> None:  # pragma: no cover
        self.description = [
            self._cap_name(),
            self.wrap(
                """
                and() tests if its contained match components evaluate to True.

                Matching is ANDed by default, but it can be set to OR. And and()
                gives you a bit more control in certain situations, such as making.
                a when/do expression that is based on multiple match components.

                The functionality of and() overlaps with all(), but all() has
                powers that are more specific than and().
            """
            ),
        ]
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
            self.match = sib.matches(skip=skip)
            if not self.match:
                break
