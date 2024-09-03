# pylint: disable=C0114
from typing import Any
from .function import Function
from ..util.expression_utility import ExpressionUtility


class Sum(Function):
    def check_valid(self) -> None:
        self.validate_one_arg()
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:
        if skip and self in skip:  # pragma: no cover
            return self._noop_value()
        if not self.value:
            var = self.first_non_term_qualifier(self.name)
            val = self.matcher.get_variable(var, set_if_none=0)
            self.value = val
            if self.do_onmatch():
                child = self.children[0]
                cval = child.to_value()
                if ExpressionUtility.is_none(cval):
                    cval = 0
                else:
                    cval = ExpressionUtility.to_float(cval)
                val += cval
                self.matcher.set_variable(var, value=val)
                self.value = val
        return self.value

    def matches(self, *, skip=None) -> bool:
        if skip and self in skip:  # pragma: no cover
            return self._noop_match()
        return self.to_value()  # pragma: no cover
