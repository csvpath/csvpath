# pylint: disable=C0114
from typing import Any
from ..function_focus import ValueProducer
from ..args import Args


class Nonef(ValueProducer):
    """returns None"""

    def check_valid(self) -> None:
        Args().validate(self.siblings())
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:  # pragma: no cover
        return None

    def matches(self, *, skip=None) -> bool:  # pragma: no cover
        return self.default_match()
