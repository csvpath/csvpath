from typing import Any
from .function import Function, ChildrenException


class Advance(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()
        self.validate_one_arg()
        if self.value is None:
            child = self.children[0]
            v = child.to_value(skip=skip)
            try:
                v = int(v)
                self.matcher.csvpath.advance(v)
            except Exception:
                raise ChildrenException(f"Advance must contain an int, not {v}")
            self.value = True
        return self.value

    def matches(self, *, skip=[]) -> bool:
        if self in skip:  # pragma: no cover
            return self._noop_match()
        return self.to_value(skip=skip)
