from typing import Any
from .function import Function, ChildrenException
from ..productions import Term


class Stop(Function):
    def to_value(self, *, skip=[]) -> Any:
        return self.matches(skip=skip)

    def matches(self, *, skip=[]) -> bool:
        if self in skip:  # pragma: no cover
            return False
        self.validate_zero_or_more_args()
        if self.match is None:
            self.match = True
            stopped = False
            if len(self.children) == 1:
                b = self.children[0].matches(skip=skip)
                if b is True:
                    self.matcher.csvpath.stop()
                    stopped = True
            else:
                self.matcher.csvpath.stop()
                stopped = True
            if stopped and self.name == "fail_and_stop":
                self.matcher.csvpath.is_valid = False
        return self.match
