# pylint: disable=C0114
from ..function_focus import MatchDecider


class Fail(MatchDecider):
    """when called this function fails the file that is being processed"""

    def check_valid(self) -> None:
        self.validate_zero_args()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.matcher.csvpath.is_valid = False
        self.value = False

    def _decide_match(self, skip=None) -> None:
        self.to_value(skip=skip)
        self.match = False
