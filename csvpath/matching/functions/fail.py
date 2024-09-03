# pylint: disable=C0114
from typing import Any
from .function import Function


class Fail(Function):
    def check_valid(self) -> None:
        self.validate_zero_args()
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:
        self.matcher.csvpath.is_valid = False
        return False

    def matches(self, *, skip=None) -> bool:
        self.to_value(skip=skip)
        return False
