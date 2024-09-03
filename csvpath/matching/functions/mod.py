# pylint: disable=C0114
from typing import Any
from .function import Function
from ..productions import Equality, ChildrenException


class Mod(Function):
    def check_valid(self) -> None:
        self.validate_two_args()
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:
        if skip and self in skip:  # pragma: no cover
            return self._noop_value()
        if not self.value:
            child = self.children[0]
            siblings = child.commas_to_list()
            ret = 0
            try:
                v = siblings[0].to_value(skip=skip)
                m = siblings[1].to_value(skip=skip)
                ret = float(v) % float(m)
            except Exception:
                raise ChildrenException("mod()'s arguments must convert to float")
            ret = round(ret, 2)
            self.value = ret
        return self.value

    def matches(self, *, skip=None) -> bool:
        return self._noop_match()  # pragma: no cover
