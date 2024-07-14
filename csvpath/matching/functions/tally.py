from typing import Any
from csvpath.matching.functions.function import Function, ChildrenException
from csvpath.matching.productions.equality import Equality


class Tally(Function):
    def to_value(self, *, skip=[]) -> Any:
        if len(self.children) != 1:
            raise ChildrenException("Tally function must have 1 child")
        if self not in skip and self.value is None:
            child = self.children[0]
            kids = child.commas_to_list() if isinstance(child, Equality) else [child]
            tally = ""
            for _ in kids:
                tally += f"{_.to_value(skip=skip)}|"
                value = f"{_.to_value(skip=skip)}"
                self._store(_.name, value)
            if len(kids) > 1:
                self._store("tally", tally[0 : len(tally) - 1])

            self.value = True  # "tally" if isinstance(child, Equality) else child.name
        return self.value

    def _store(self, name, value):
        count = self.matcher.get_variable(name, tracking=value)
        if count is None:
            count = 0
        count += 1
        self.matcher.set_variable(
            name,
            tracking=value,
            value=count,
        )

    def matches(self, *, skip=[]) -> bool:
        return self.to_value(skip=skip) is not None
