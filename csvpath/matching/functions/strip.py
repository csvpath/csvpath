# pylint: disable=C0114
from typing import Any
from .function import Function


class Strip(Function):
    def check_valid(self) -> None:
        self.validate_one_arg()
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:
        if skip and self in skip:  # pragma: no cover
            return self._noop_value()
        if self.value is None:
            v = self.children[0].to_value()
            string = f"{v}"
            self.value = string.strip()
        return self.value

    def matches(self, *, skip=None) -> bool:
        if skip and self in skip:  # pragma: no cover
            return self._noop_match()
        self.to_value(skip=skip)
        return True
