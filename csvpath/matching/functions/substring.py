from typing import Any
from .function import Function, ChildrenException


class Substring(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()
        self.validate_two_args()
        if self.value is None:
            i = self.children[0].right.to_value()
            if not isinstance(i, int):
                raise ChildrenException("substring() must have an int second argument")
            i = int(i)
            string = self.children[0].left.to_value()
            string = f"{string}"
            if i >= len(string):
                self.value = string
            else:
                self.value = string[0:i]
        return self.value

    def matches(self, *, skip=[]) -> bool:
        if self in skip:  # pragma: no cover
            return self._noop_match()
        v = self.to_value(skip=skip)
        return v is not None
