from typing import Any
from .function import Function, ChildrenException
from ..productions import Equality


class Tally(Function):
    def to_value(self, *, skip=[]) -> Any:
        if len(self.children) != 1:
            raise ChildrenException("Tally function must have 1 child")
        if self.value is not None:
            return True
        elif self in skip:
            return True
        else:
            om = self.has_onmatch()
            if not om or self.line_matches():
                child = self.children[0]
                kids = (
                    child.commas_to_list() if isinstance(child, Equality) else [child]
                )
                tally = ""
                for _ in kids:
                    tally += f"{_.to_value(skip=skip)}|"
                    value = f"{_.to_value(skip=skip)}"
                    self._store(_.name, value)
                if len(kids) > 1:
                    self._store(
                        self.first_non_term_qualifier("tally"),
                        tally[0 : len(tally) - 1],
                    )

            self.value = True
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
        return self.to_value(skip=skip)
