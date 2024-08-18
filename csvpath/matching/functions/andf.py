from typing import Any
from .function import Function
from ..productions import Equality


class And(Function):
    def check_valid(self) -> None:
        self.validate_two_or_more_args()
        super().check_valid()

    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()
        if self.value is None:
            self.value = self.matches(skip=skip)
        return self.value

    def matches(self, *, skip=[]) -> bool:
        if self in skip:  # pragma: no cover
            return self._noop_match()
        if self.match is None:
            child = self.children[0]
            siblings = child.commas_to_list()
            for i, sib in enumerate(siblings):
                self.match = sib.matches(skip=skip)
                if not self.match:
                    break
        return self.match  # pragma: no cover
