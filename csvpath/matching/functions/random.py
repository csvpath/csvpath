from typing import Any
from csvpath.matching.functions.function import Function, ChildrenException
from random import randrange


class Random(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self in skip:
            return True
        if len(self.children) != 1:
            self.matcher.print(
                f"Random.to_value: must have 1 equality child: {self.children}"
            )
            raise ChildrenException("Random function must have 1 child")
        if self.value is None:
            lower = self.children[0].left.to_value()
            upper = self.children[0].right.to_value()
            if lower is None:
                lower == 0
            if upper is None or upper <= lower:
                upper == 1
            try:
                lower = int(lower)
                upper = int(upper)
                # we are inclusive, but randrange is not
                upper += 1
                self.value = randrange(lower, upper, 1)
            except Exception:
                pass
        return self.value

    def matches(self, *, skip=[]) -> bool:
        return True
