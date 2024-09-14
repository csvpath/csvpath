# pylint: disable=C0114
from ..function_focus import MatchDecider


class Fail(MatchDecider):
    """when called this function fails the file that is being processed"""

    def check_valid(self) -> None:
        self.validate_zero_args()
        super().check_valid()

    def override_frozen(self) -> bool:
        """fail() and last() must override to return True"""
        return True

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
        self.matcher.csvpath.is_valid = False
        #
        # the default match is approprate because this component
        # is only responsible for registering the fail, it not a
        # reason for it.
        #
        self.match = self._apply_default_match()
