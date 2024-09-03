# pylint: disable=C0114
from typing import Any
from .function import Function
import datetime


class Date(Function):
    """parses a date from a string"""

    def check_valid(self) -> None:
        self.validate_two_args()
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:
        if skip and self in skip:  # pragma: no cover
            return self._noop_value()
        if skip is None:
            skip = []
        if self.value is None:
            eq = self.children[0]
            v = eq.left.to_value(skip=skip)
            v = f"{v}".strip()
            fmt = eq.right.to_value(skip=skip)
            fmt = f"{fmt}".strip()
            try:
                d = datetime.datetime.strptime(v, fmt)
                if not self.name == "datetime":
                    d = d.date()
                self.value = d
            except Exception:
                self.value = v
        return self.value

    def matches(self, *, skip=None) -> bool:
        return self._noop_match()  # pragma: no cover
