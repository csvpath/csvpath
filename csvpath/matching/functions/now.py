from typing import Any
from .function import Function, ChildrenException
import datetime


class Now(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()
        self.validate_zero_or_one_arg()

        format = None
        if len(self.children) == 1:
            format = self.children[0].to_value(skip=skip)
            format = f"{format}".strip()
        x = datetime.datetime.now()
        xs = None
        if format:
            xs = x.strftime(format)
        else:
            xs = f"{x}"
        return xs

    def matches(self, *, skip=[]) -> bool:
        return self._noop_match()  # pragma: no cover
