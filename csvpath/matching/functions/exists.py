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

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    def matches(self, *, skip=None) -> bool:
        if skip and self in skip:  # pragma: no cover
            return self._noop_match()
        if self.match is None:
            v = self.children[0].to_value()
            ab = self.children[0].asbool
            if ab:
                v = bool(v)
                self.match = v
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
        except TypeError:
            return False
