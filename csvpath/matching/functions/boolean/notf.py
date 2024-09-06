# pylint: disable=C0114
from ..function_focus import MatchDecider


class Not(MatchDecider):
    """returns the boolean inverse of a value"""

    def check_valid(self) -> None:
        self.validate_one_arg()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        m = self.children[0].matches(skip=skip)
        m = not m
        self.value = m

    def matches(self, *, skip=None) -> bool:
        if skip and self in skip:  # pragma: no cover
            return self._noop_match()
        return self.to_value(skip=skip)
