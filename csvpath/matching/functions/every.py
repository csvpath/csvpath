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

            ###
            # 1. we store a count of values under the ID of left. this is the value.to_value
            # 2. we store the every-N-seen count under the qualifier or ID of every
            # 3. we match based on count % n == 0
            #
            self._id = (
                self.qualifier if self.qualifier is not None else self.get_id(self)
            )
            allcount = f"{self.get_id(self)}_{'every'}"
            tracked_value = self.children[0].left.to_value(skip=skip)
            print(f"Every.matches: tracked_value: {tracked_value}")
            cnt = self.matcher.get_variable(
                allcount, tracking=tracked_value, set_if_none=0
            )
            cnt += 1
            self.matcher.set_variable(allcount, tracking=tracked_value, value=cnt)
            every = self.children[0].right.to_value()
            print(
                f"Every.matches: {self._id}: every: {every}, cnt: {cnt} % {every} = {cnt % every}"
            )
            if cnt % every == 0:
                self.value = True
            else:
                self.value = False
            everycount = self.matcher.get_variable(
                self._id, tracking=self.value, set_if_none=0
            )
            everycount += 1
            self.matcher.set_variable(self._id, tracking=self.value, value=everycount)
        return self.value
