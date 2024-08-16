from typing import Any
from .function import Function, ChildrenException


class Failed(Function):
    def to_value(self, *, skip=[]) -> Any:
        self.validate_zero_args()
        if self.name == "failed":
            return not self.matcher.csvpath.is_valid
        elif self.name == "valid":
            return self.matcher.csvpath.is_valid
        else:
            raise Exception(f"Incorrect name {self.name} for a Failed class instance")

    def matches(self, *, skip=[]) -> bool:
        self.validate_zero_args()
        return self.to_value(skip=skip)
