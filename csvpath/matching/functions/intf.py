# pylint: disable=C0114
from typing import Any
from .function import Function
from ..productions import ChildrenException


class Int(Function):
    def check_valid(self) -> None:
        self.validate_one_arg()
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:
        if skip and self in skip:  # pragma: no cover
            return self._noop_value()
        if not self.value:
            child = self.children[0]
            i = child.to_value()
            try:
                i = int(i)
            except Exception:
                if i is None:
                    i = 0
                elif f"{i}".strip() == "":
                    i = 0
                elif i is False:
                    i = 0
                if i != 0:
                    raise ChildrenException("int()'s argument must convert to int")
            self.value = i
        return self.value

    def matches(self, *, skip=None) -> bool:
        return self._noop_match()  # pragma: no cover
