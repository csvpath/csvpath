# pylint: disable=C0114
from typing import Any
from ..function_focus import ValueProducer
from ..args import Args


class HasMatches(ValueProducer):
    """True if there have been matches."""

    def check_valid(self) -> None:  # pylint: disable=W0246
        self.description = [
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
        #
        # True only when an earlier line matched. _current_match_count is the
        # match count as it stood when this line started. current_match_count
        # is the live count, which an onmatch component can raise partway
        # through this line, so it would count this line as "previous".
        #
        self.match = self.matcher.csvpath._current_match_count > 0
