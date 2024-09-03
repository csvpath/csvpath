# pylint: disable=C0114
from typing import Any
from .function import Function, ChildrenException


class StartsWith(Function):
    """checks if a string begins with another string"""

    def check_valid(self) -> None:
        self.validate_two_args()
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:
        if skip and self in skip:  # pragma: no cover
            return self._noop_value()
        if self.value is None:
            v = self.children[0].left.to_value()
            v = f"{v}".strip()
            sw = self.children[0].right.to_value()
            sw = f"{sw}".strip()
            self.value = v.startswith(sw)
        return self.value

    def matches(self, *, skip=None) -> bool:
        if skip and self in skip:  # pragma: no cover
            return self._noop_match()
        if self.match is None:
            self.match = self.to_value(skip=skip)
        return self.match
