# pylint: disable=C0114
from .function import Function
from ..productions import Header


class PercentUnique(Function):
    """return the % of a value that is unique over lines so far seen"""

    def check_valid(self) -> None:
        self.validate_one_arg(types=[Header])
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
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

    def matches(self, *, skip=None) -> bool:
        if skip and self in skip:  # pragma: no cover
            return self._noop_match()
        v = self.to_value(skip=skip)
        return v is not None
