from typing import Any
from .function import Function, ChildrenException


class Int(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()
        if not self.value:
            self.validate_one_arg()
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
                    raise ChildrenException(
                        "int()'s argument must be convertable to int"
                    )
            self.value = i
        return self.value

    def matches(self, *, skip=[]) -> bool:
        return self._noop_match()  # pragma: no cover
