from typing import Any
from .function import Function, ChildrenException
from ..productions import Equality


class Collect(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_match()
        if self.children and len(self.children) != 1:
            raise ChildrenException(
                "Collect must have 1 child, a term or an equality with the ',' operator"
            )
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

    def matches(self, *, skip=[]) -> bool:
        if self in skip:  # pragma: no cover
            return self._noop_match()
        return self.to_value(skip=skip)
