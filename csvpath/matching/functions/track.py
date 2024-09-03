# pylint: disable=C0114
from typing import Any
from .function import Function
from ..productions import ChildrenException


class Track(Function):
    def check_valid(self) -> None:
        self.validate_two_args()
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:
        if skip and self in skip:  # pragma: no cover
            return self._noop_value()
        if self.value is None:
            if not self.onmatch or self.line_matches():
                left = self.children[0].children[0]
                right = self.children[0].children[1]
                varname = self.first_non_term_qualifier(self.name)
                tracking = f"{left.to_value()}".strip()
                v = right.to_value()
                if isinstance(v, str):
                    v = f"{v}".strip()
                value = v
                self.matcher.set_variable(varname, tracking=tracking, value=value)
                self.value = True
        return self.value

    def matches(self, *, skip=None) -> bool:
        if skip and self in skip:  # pragma: no cover
            return self._noop_match()
        return self.to_value(skip=skip)
