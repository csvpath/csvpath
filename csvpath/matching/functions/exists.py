# pylint: disable=C0114
from typing import Any
import math
from .function import Function
from ..productions import Header, Variable


class Exists(Function):
    """tests if a value exists"""

    def check_valid(self) -> None:
        self.validate_one_arg(types=[Variable, Header])
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:
        if skip and self in skip:  # pragma: no cover
            return self._noop_value()
        if self.value is None:
            self.value = self.matches(skip=skip)
        return self.value

    def matches(self, *, skip=[]) -> bool:
        if skip and self in skip:  # pragma: no cover
            return self._noop_match()
        if self.match is None:
            v = self.children[0].to_value()
            ab = self.children[0].asbool
            if ab:
                try:
                    v = bool(v)
                    self.match = v
                except Exception:
                    self.match = False
            elif v is None:
                self.match = False
            elif self._isnan(v):
                self.match = False
            elif f"{v}".strip() != "":
                self.match = True
            else:
                self.match = False
        return self.match

    def _isnan(self, v) -> bool:
        try:
            return math.isnan(v)
        except Exception:
            return False
