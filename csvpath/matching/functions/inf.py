# pylint: disable=C0114
from typing import Any
from .function import Function


class In(Function):
    def check_valid(self) -> None:
        self.validate_two_args()
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:
        if skip and self in skip:  # pragma: no cover
            return self._noop_value()
        if self.value is None:
            vchild = self.children[0].children[0]
            lchild = self.children[0].children[1]
            mylist = []
            liststr = lchild.to_value(skip=skip)
            mylist = liststr.split("|")
            v = vchild.to_value()
            ret = None
            if v in mylist:
                ret = True
            elif v.__class__ != str and f"{v}" in mylist:
                ret = True
            else:
                ret = False
            self.value = ret
        return self.value

    def matches(self, *, skip=None) -> bool:
        if skip and self in skip:  # pragma: no cover
            return self._noop_match()
        return self.to_value(skip=skip)
