# pylint: disable=C0114
import datetime
from ..function_focus import ValueProducer


class Date(ValueProducer):
    """parses a date from a string"""

    def check_valid(self) -> None:
        self.validate_two_args()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        eq = self.children[0]
        v = eq.left.to_value(skip=skip)
        v = f"{v}".strip()
        fmt = eq.right.to_value(skip=skip)
        fmt = f"{fmt}".strip()
        try:
            d = datetime.datetime.strptime(v, fmt)
            if not self.name == "datetime":
                d = d.date()
            self.value = d
        except (UnicodeError, ValueError):
            self.value = v

    def matches(self, *, skip=None) -> bool:
        return self._noop_match()  # pragma: no cover
