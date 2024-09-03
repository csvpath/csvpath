# pylint: disable=C0114
from typing import Any
from .function import Function
from ..productions import Equality


class Collect(Function):
    """use this class to identify what headers should be collected when
    a line matches. by default all headers are collected."""

    def check_valid(self) -> None:
        self.validate_one_or_more_args()
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:
        if skip and self in skip:  # pragma: no cover
            return self._noop_match()
        if self.value is None:
            collect = []
            if isinstance(self.children[0], Equality):
                siblings = self.children[0].commas_to_list()
                for s in siblings:
                    collect.append(s.to_value())
            else:
                collect.append(self.children[0].to_value())
            cs = []
            for s in collect:
                if not isinstance(s, int):
                    cs.append(self.matcher.header_index(s))
                else:
                    cs.append(int(s))
            self.matcher.csvpath.limit_collection_to = cs
            self.value = True
        return self.value  # pragma: no cover

    def matches(self, *, skip=None) -> bool:
        if skip and self in skip:  # pragma: no cover
            return self._noop_match()
        return self.to_value(skip=skip)
