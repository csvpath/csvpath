# pylint: disable=C0114
from typing import Any
from ..function_focus import ValueProducer
from ..args import Args


class HasMatches(ValueProducer):
    """True if there have been matches."""

    def check_valid(self) -> None:  # pylint: disable=W0246
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
            True when the run has so far had one or more lines that matched. If a run
            is collecting data, at least one line of data is collected.
            """
            ),
        ]
        self.args = Args(matchable=self)
        self.args.validate(self.siblings())
        super().check_valid()  # pylint: disable=W0246

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
        self.match = self.matcher.csvpath.current_match_count + 1 > 0
