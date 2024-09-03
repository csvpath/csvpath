# pylint: disable=C0114
from typing import Any
from .function import Function
from ..productions import Equality


class Tally(Function):
    def check_valid(self) -> None:
        self.validate_one_or_more_args()
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:
        if skip and self in skip:  # pragma: no cover
            return self._noop_value()
        if self.value is not None:
            return True
        else:
            om = self.has_onmatch()
            if not om or self.line_matches():
                child = self.children[0]
                siblings = None
                if isinstance(child, Equality):
                    siblings = child.commas_to_list()
                else:
                    siblings = [child]
                tally = ""
                for _ in siblings:
                    tally += f"{_.to_value(skip=skip)}|"
                    value = f"{_.to_value(skip=skip)}"
                    self._store(_.name, value)
                if len(siblings) > 1:
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

    def matches(self, *, skip=None) -> bool:
        if skip and self in skip:  # pragma: no cover
            return self._noop_match()
        return self.to_value(skip=skip)
