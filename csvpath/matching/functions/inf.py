from typing import Any
from .function import Function


class In(Function):
    def check_valid(self) -> None:
        self.validate_two_args()
        super().check_valid()

    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()
        vchild = self.children[0].children[0]
        lchild = self.children[0].children[1]
        mylist = []
        liststr = lchild.to_value(skip=skip)
        mylist = liststr.split("|")
        v = vchild.to_value()
        if v in mylist:
            return True
        elif v.__class__ != str and f"{v}" in mylist:
            return True
        else:
            return False

    def matches(self, *, skip=[]) -> bool:
        if self in skip:  # pragma: no cover
            return self._noop_match()

        return self.to_value(skip=skip)
