# pylint: disable=C0114
from ..function import Function


class Strip(Function):
    """removes whitespace from the beginning and end of a string"""

    def check_valid(self) -> None:
        self.validate_one_arg()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        v = self.children[0].to_value()
        string = f"{v}"
        self.value = string.strip()

    def matches(self, *, skip=None) -> bool:
        if skip and self in skip:  # pragma: no cover
            return self._noop_match()
        self.to_value(skip=skip)
        return True
