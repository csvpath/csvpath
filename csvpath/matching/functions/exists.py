from typing import Any
import math
from .function import Function, ChildrenException
from ..productions import Header, Variable


class Exists(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()
        if self.value is None:
            self.value = self.matches(skip=skip)
        return self.value

    def matches(self, *, skip=[]) -> bool:
        if self in skip:  # pragma: no cover
            return self._noop_match()
        if self.children and len(self.children) != 1:
            raise ChildrenException("Exists must have a header or variable child")
        if not isinstance(self.children[0], Header) and not isinstance(
            self.children[0], Variable
        ):
            raise ChildrenException("Exists must have a header or variable child")
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
