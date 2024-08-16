from typing import Any
from .function import Function, ChildrenException
from ..productions.term import Term


class End(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()
        self.validate_zero_or_one_arg([Term])
        if not self.value:
            i = self.matcher.last_header_index()
            if len(self.children) > 0:
                v = self.children[0].to_value()
                if isinstance(v, int) or v.isdigit():
                    i = i - int(v)
                else:
                    raise ChildrenException(
                        "Value of end function term must be a positive int"
                    )
            if i >= 0 and i < len(self.matcher.line):
                self.value = self.matcher.line[i]
        return self.value

    def matches(self, *, skip=[]) -> bool:
        if self in skip:  # pragma: no cover
            return self._noop_match()
        return self.to_value(skip=skip) is not None
