# pylint: disable=C0114
from typing import Any
from .function import Function
from ..productions import Term, ChildrenException


class End(Function):
    """returns the value of the last header"""

    def check_valid(self) -> None:
        self.validate_zero_or_one_arg([Term])
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:
        if skip and self in skip:  # pragma: no cover
            return self._noop_value()
        if self.value is None:
            i = self.matcher.last_header_index()
            if i is None:
                #
                # this could happen when a line is blank or has some other oddity
                #
                pass
            else:
                if len(self.children) > 0:
                    v = self.children[0].to_value()
                    if isinstance(v, int) or v.isdigit():
                        i = i - int(v)
                    else:
                        raise ChildrenException("end()'s term must be a positive int")
                if i >= 0 and i < len(self.matcher.line):
                    self.value = self.matcher.line[i]
        return self.value

    def matches(self, *, skip=None) -> bool:
        if skip and self in skip:  # pragma: no cover
            return self._noop_match()
        return self.to_value(skip=skip) is not None
