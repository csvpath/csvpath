# pylint: disable=C0114
from .function import Function
from random import randrange


class Random(Function):
    """returns a random int within a range"""

    def check_valid(self) -> None:
        self.validate_two_args()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        lower = self.children[0].left.to_value(skip=skip)
        upper = self.children[0].right.to_value(skip=skip)
        if lower is None:
            lower == 0
        if upper is None or upper <= lower:
            upper == 1
        lower = int(lower)
        upper = int(upper)
        # we are inclusive, but randrange is not
        upper += 1
        self.value = randrange(lower, upper, 1)

    def matches(self, *, skip=None) -> bool:
        return self._noop_value()  # pragma: no cover
