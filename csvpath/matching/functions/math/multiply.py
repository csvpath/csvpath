# pylint: disable=C0114
from ..function_focus import ValueProducer


class Multiply(ValueProducer):
    """multiplies numbers"""

    def check_valid(self) -> None:
        self.validate_two_or_more_args()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        child = self.children[0]
        siblings = child.commas_to_list()
        ret = 0
        for i, sib in enumerate(siblings):
            v = sib.to_value(skip=skip)
            if i == 0:
                ret = v
            else:
                ret = float(v) * float(ret)
        self.value = ret

    def _decide_match(self, skip=None) -> None:
        self.match = self._noop_match()
