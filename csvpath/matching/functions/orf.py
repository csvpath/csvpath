# pylint: disable=C0114
from typing import Any
from .function import Function
from ..productions import Equality


class Or(Function):
    """does a logical OR of match components"""

    def check_valid(self) -> None:
        self.validate_two_or_more_args()
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:
        if skip and self in skip:  # pragma: no cover
            return self._noop_value()
        return self.matches(skip=skip)

    def matches(self, *, skip=None) -> bool:
        if skip and self in skip:  # pragma: no cover
            return self._noop_match()
        else:
            skip.append(self)
        if not self.value:
            child = self.children[0]
            siblings = child.commas_to_list()
            ret = False
            for i, sib in enumerate(siblings):
                if sib.matches(skip=skip):
                    ret = True
                    break
            self.value = ret
        return self.value
