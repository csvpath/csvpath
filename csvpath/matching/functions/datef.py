from typing import Any
from .function import Function, ChildrenException
import datetime


class Date(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()
        self.validate_two_args()
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

    def matches(self, *, skip=[]) -> bool:
        return self._noop_match()  # pragma: no cover
