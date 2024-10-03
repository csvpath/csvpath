# pylint: disable=C0114
from typing import Any
from ..function_focus import ValueProducer
from ..args import Args


class Nonef(ValueProducer):
    """returns None"""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        self.args.argset(0)
        self.args.validate(self.siblings())
        super().check_valid()

    # def to_value(self, *, skip=None) -> Any:  # pragma: no cover
    def _produce_value(self, skip=None) -> None:
        self.value = None

    def _decide_match(self, *, skip=None) -> None:  # pragma: no cover
        self.match = False
