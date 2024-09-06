# pylint: disable=C0114
from ..function_focus import ValueProducer


class StartsWith(ValueProducer):
    """checks if a string begins with another string"""

    def check_valid(self) -> None:
        self.validate_two_args()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        v = self.children[0].left.to_value(skip=skip)
        v = f"{v}".strip()
        sw = self.children[0].right.to_value(skip=skip)
        sw = f"{sw}".strip()
        self.value = v.startswith(sw)

    def matches(self, *, skip=None) -> bool:
        if skip and self in skip:  # pragma: no cover
            return self._noop_match()
        if self.match is None:
            self.match = self.to_value(skip=skip)
        return self.match