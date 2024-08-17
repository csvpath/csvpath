from typing import Any
from .function import Function
from ..productions import Header


class PercentUnique(Function):
    def check_valid(self) -> None:
        self.validate_one_arg(types=[Header])
        super().check_valid()

    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()

        if self.value is None:
            om = self.has_onmatch()
            if not om or self.line_matches():
                tracking = self.children[0].to_value()
                name = self.first_non_term_qualifier("percent_unique")

                v = self.matcher.get_variable(name, tracking=tracking, set_if_none=0)
                v += 1
                self.matcher.set_variable(name, tracking=tracking, value=v)

                d = self.matcher.get_variable(name)
                uniques = 0
                for v, k in enumerate(d):
                    if d[k] == 1:
                        uniques += 1
                t = self.matcher.csvpath.match_count
                t += 1

                self.value = round(uniques / t, 2) * 100
        return self.value

    def matches(self, *, skip=[]) -> bool:
        if self in skip:  # pragma: no cover
            return self._noop_match()
        v = self.to_value(skip=skip)
        return v is not None
