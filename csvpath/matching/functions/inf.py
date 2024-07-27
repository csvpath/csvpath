from typing import Any
from .function import Function, ChildrenException


class In(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self in skip:
            return True
        if len(self.children) != 1:
            self.matcher.print(
                f"In.to_value: must have 1 equality child: {self.children}"
            )
            raise ChildrenException("In function must have 1 child")
        if self.children[0].op != ",":
            raise ChildrenException(
                f"In function must have an equality with the ',' operation, not {self.children[0].op}"
            )
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
        return self.to_value(skip=skip)
