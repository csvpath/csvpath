# pylint: disable=C0114
from typing import Any
from ..function_focus import MatchDecider


class No(MatchDecider):
    """returns False"""

    def check_valid(self) -> None:
        self.validate_zero_args()
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:  # pragma: no cover
        return False

    def matches(self, *, skip=None) -> bool:  # pragma: no cover
        return False