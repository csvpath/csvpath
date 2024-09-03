# pylint: disable=C0114
from typing import Any
from .function import Function


class Upper(Function):
    """uppercases a string"""

    def check_valid(self) -> None:
        self.validate_one_arg()
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:
        if skip and self in skip:  # pragma: no cover
            return self._noop_value()
        value = self.children[0].to_value(skip=skip)
        value = f"{value}".upper()
        return value

    def matches(self, *, skip=None) -> bool:
        if skip and self in skip:  # pragma: no cover
            return self._noop_match()
        v = self.to_value(skip=skip)
        return v is not None
