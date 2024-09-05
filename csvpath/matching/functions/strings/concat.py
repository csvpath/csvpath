# pylint: disable=C0114
from ..function import Function


class Concat(Function):
    """concats two strings"""

    def check_valid(self) -> None:
        self.validate_two_or_more_args()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        child = self.children[0]
        siblings = child.commas_to_list()
        v = ""
        for s in siblings:
            v = f"{v}{s.to_value(skip=skip)}"
        self.value = v

    def matches(self, *, skip=None) -> bool:
        self.to_value(skip=skip)
        return self._noop_match()
