# pylint: disable=C0114
from typing import Any
from ..function_focus import SideEffect
from ..args import Args


class Variables(SideEffect):
    """indicates a function like any() or all() should look to the variables"""

    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                Directs certain functions, such as any() or all(), to search in the variables.
                headers() has the same function, but directing the search to the headers.
                """
            ),
        ]
        self.args = Args(matchable=self)
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self._apply_default_value()

    def _decide_match(self, skip=None) -> None:
        self.match = self.default_match()
