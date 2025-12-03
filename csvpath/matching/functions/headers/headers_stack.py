# pylint: disable=C0114
from typing import Any
from ..function_focus import ValueProducer
from ..args import Args


class HeadersStack(ValueProducer):
    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                Returns the current header names as a stack variable.
            """
            ),
        ]
        self.args = Args(matchable=self)
        self.args.argset(0)
        self.args.validate(self.siblings())
        super().check_valid()  # pragma: no cover

    def _produce_value(self, skip=None) -> None:
        stack = self.matcher.csvpath.headers[:]
        self.value = stack

    def _decide_match(self, skip=None) -> None:
        self.match = self.default_match()
