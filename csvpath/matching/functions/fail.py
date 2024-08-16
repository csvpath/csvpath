from typing import Any
from .function import Function, ChildrenException


class Fail(Function):
    def to_value(self, *, skip=[]) -> Any:
        self.validate_zero_args()
        self.matcher.csvpath.is_valid = False
        return False

    def matches(self, *, skip=[]) -> bool:
        self.to_value(skip=skip)
        return False
