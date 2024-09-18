# pylint: disable=C0114
from ..function_focus import MatchDecider


class Not(MatchDecider):
    """returns the boolean inverse of a value"""

    def check_valid(self) -> None:
        self.validate_one_arg()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
        m = self.children[0].matches(skip=skip)
        m = not m
        self.match = m
        # print(f"Not._decide_mat: self.match: {self.match} -> {self}")
