# pylint: disable=C0114
from typing import Any
from ..function_focus import SideEffect
from ..args import Args


class Variables(SideEffect):
    """indicates a function like any() or all() should look to the variables"""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        self.args.validate(self.siblings())
        super().check_valid()

    """
    def to_value(self, *, skip=None) -> Any:  # pragma: no cover
        return True
    """

    def _produce_value(self, skip=None) -> None:
        self._apply_default_value()

    def _decide_match(self, skip=None) -> None:
        self.match = self.default_match()

    """
    def matches(self, *, skip=None) -> bool:  # pragma: no cover
        return self.default_match()
    """
