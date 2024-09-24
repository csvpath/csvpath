# pylint: disable=C0114
from typing import Any
from ..function_focus import ValueProducer


class HasMatches(ValueProducer):
    """True if there have been matches."""

    def check_valid(self) -> None:  # pylint: disable=W0246
        self.validate_zero_args()
        super().check_valid()  # pylint: disable=W0246

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
        self.match = self.matcher.csvpath.current_match_count + 1 > 0
