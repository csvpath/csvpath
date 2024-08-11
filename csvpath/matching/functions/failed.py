from typing import Any
from .function import Function, ChildrenException


class Failed(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self.name == "failed":
            return not self.matcher.csvpath.is_valid
        elif self.name == "valid":
            return self.matcher.csvpath.is_valid
        else:
            raise Exception(f"Incorrect name {self.name} for a Failed class instance")

    def matches(self, *, skip=[]) -> bool:
        return self.to_value(skip=skip)
