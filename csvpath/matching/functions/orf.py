# pylint: disable=C0114
from typing import Any
from .function import Function


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
        skip.append(self)
        if not self.value:
            child = self.children[0]
            siblings = child.commas_to_list()
            ret = False
            for sib in siblings:
                if sib.matches(skip=skip):
                    ret = True
                    break
            self.value = ret
        return self.value
