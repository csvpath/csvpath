from typing import Any
from .function import Function


class Yes(Function):
    def check_valid(self) -> None:
        self.validate_zero_args()
        super().check_valid()

    def to_value(self, *, skip=[]) -> Any:  # pragma: no cover
        return True

    def matches(self, *, skip=[]) -> bool:  # pragma: no cover
        return True
