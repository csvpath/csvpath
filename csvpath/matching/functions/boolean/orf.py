# pylint: disable=C0114
from ..function_focus import MatchDecider


class Or(MatchDecider):
    """does a logical OR of match components"""

    def check_valid(self) -> None:
        self.validate_two_or_more_args()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
        child = self.children[0]
        siblings = child.commas_to_list()
        ret = False
        for sib in siblings:
            if sib.matches(skip=skip):
                ret = True
                break
        self.match = ret
