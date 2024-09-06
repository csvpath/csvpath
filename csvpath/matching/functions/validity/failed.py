# pylint: disable=C0114
from csvpath.matching.util.exceptions import ChildrenException
from ..function_focus import MatchDecider


class Failed(MatchDecider):
    """matches when the current file is in the failed/invalid state"""

    def check_valid(self) -> None:
        self.validate_zero_args()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
        if self.name == "failed":
            self.match = not self.matcher.csvpath.is_valid
        elif self.name == "valid":
            self.match = self.matcher.csvpath.is_valid
        else:
            raise ChildrenException(f"Incorrect function name {self.name}")
