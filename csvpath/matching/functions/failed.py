# pylint: disable=C0114
from typing import Any
from .function import Function
from ..productions import ChildrenException


class Failed(Function):
    """matches when the current file is in the failed/invalid state"""

    def check_valid(self) -> None:
        self.validate_zero_args()
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:
        if self.name == "failed":
            return not self.matcher.csvpath.is_valid
        if self.name == "valid":
            return self.matcher.csvpath.is_valid
        raise ChildrenException(f"Incorrect function name {self.name}")

    def matches(self, *, skip=None) -> bool:
        return self.to_value(skip=skip)
