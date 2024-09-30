# pylint: disable=C0114
from typing import Any
from ..function_focus import MatchDecider
from ..args import Args


class No(MatchDecider):
    """returns False"""

    def check_valid(self) -> None:
        Args().validate(self.siblings())
        super().check_valid()

    # def to_value(self, *, skip=None) -> Any:  # pragma: no cover
    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    def matches(self, *, skip=None) -> bool:  # pragma: no cover
        return False
