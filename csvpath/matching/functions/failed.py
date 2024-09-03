# pylint: disable=C0114
from typing import Any
from .function import Function


class Failed(Function):
    def check_valid(self) -> None:
        self.validate_zero_args()
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:
        if self.name == "failed":
            return not self.matcher.csvpath.is_valid
        elif self.name == "valid":
            return self.matcher.csvpath.is_valid
        else:
            raise Exception(f"Incorrect name {self.name} for a Failed class instance")

    def matches(self, *, skip=None) -> bool:
        return self.to_value(skip=skip)
