from typing import Any
from .function import Function, ChildrenException
import datetime


class Now(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self in skip:
            return True
        if len(self.children) > 1:
            ChildrenException(
                "now function may have only a single child that gives a format"
            )
        format = None
        if self.children and len(self.children) == 1:
            format = self.children[0].to_value(skip=skip)
        x = datetime.datetime.now()
        xs = None
        if format:
            xs = x.strftime(format)
        else:
            xs = f"{x}"
        return xs

    def matches(self, *, skip=[]) -> bool:
        return True  # always matches because not internally matchable
