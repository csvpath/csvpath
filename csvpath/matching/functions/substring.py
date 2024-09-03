# pylint: disable=C0114
from typing import Any
from .function import Function, ChildrenException


class Substring(Function):
    def check_valid(self) -> None:
        self.validate_two_args()
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:
        if skip and self in skip:  # pragma: no cover
            return self._noop_value()
        if self.value is None:
            i = self.children[0].right.to_value()
            if not isinstance(i, int):
                raise ChildrenException("substring()'s 2nd argument must be an int")
            i = int(i)
            string = self.children[0].left.to_value()
            string = f"{string}"
            if i >= len(string):
                self.value = string
            else:
                self.value = string[0:i]
        return self.value

    def matches(self, *, skip=None) -> bool:
        if skip and self in skip:  # pragma: no cover
            return self._noop_match()
        v = self.to_value(skip=skip)
        return v is not None
