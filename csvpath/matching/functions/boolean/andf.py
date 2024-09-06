# pylint: disable=C0114

from typing import Any
from ..function_focus import MatchDecider


class And(MatchDecider):
    """ANDs match components. remember that csvpath is
    AND by default; however, there are times when you
    need more control."""

    def check_valid(self) -> None:  # pragma: no cover
        self.validate_two_or_more_args()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:  # pragma: no cover
        self.value = self.matches(skip=skip)

    def matches(self, *, skip=None) -> bool:
        if skip and self in skip:  # pragma: no cover
            return self._noop_match()
        if self.match is None:
            child = self.children[0]
            siblings = child.commas_to_list()
            for sib in siblings:
                self.match = sib.matches(skip=skip)
                if not self.match:
                    break
        return self.match  # pragma: no cover
