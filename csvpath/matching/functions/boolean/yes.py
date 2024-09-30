# pylint: disable=C0114
from typing import Any
from ..function import Function
from ..args import Args


class Yes(Function):
    """returns True"""

    def check_valid(self) -> None:
        Args().validate(self.siblings())
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:  # pragma: no cover
        return True

    def matches(self, *, skip=None) -> bool:  # pragma: no cover
        return True
