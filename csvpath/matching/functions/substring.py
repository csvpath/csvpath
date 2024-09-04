# pylint: disable=C0114
from typing import Any
from .function import Function
from ..util.exceptions import ChildrenException


class Substring(Function):
    """returns a substring of a value from 0 to N"""

    def check_valid(self) -> None:
        self.validate_two_args()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        i = self.children[0].right.to_value(skip=skip)
        if not isinstance(i, int):
            raise ChildrenException("substring()'s 2nd argument must be an int")
        i = int(i)
        string = self.children[0].left.to_value(skip=skip)
        string = f"{string}"
        if i >= len(string):
            self.value = string
        else:
            self.value = string[0:i]

    def matches(self, *, skip=None) -> bool:
        if skip and self in skip:  # pragma: no cover
            return self._noop_match()
        v = self.to_value(skip=skip)
        self.match = v is not None
        return self.match
