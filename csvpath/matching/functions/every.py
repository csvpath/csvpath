from typing import Any
from csvpath.matching.functions.function import Function, ChildrenException
from csvpath.matching.productions.equality import Equality


class Every(Function):
    def to_value(self, *, skip=[]) -> Any:
        return self.matches(skip=skip)

    def matches(self, *, skip=[]) -> bool:
        if self.value is None:
            if len(self.children) != 1:
                raise ChildrenException("no children. there must be 1 equality child")
            child = self.children[0]
            if not isinstance(child, Equality):
                raise ChildrenException("must be 1 equality child")

            tracked_value = self.children[0].left.matches(skip=skip)
            if tracked_value:
                every = self.children[0].right.to_value()
                self._id = (
                    self.qualifier if self.qualifier is not None else self.get_id(self)
                )
                cnt = self.matcher.get_variable(
                    self._id, tracking=tracked_value, set_if_none=0
                )
                cnt += 1
                self.matcher.set_variable(self._id, tracking=tracked_value, value=cnt)
                if cnt % every == 0:
                    self.value = True
                else:
                    self.value = False
            else:
                self.value = False
        return self.value
