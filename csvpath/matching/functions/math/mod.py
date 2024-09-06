# pylint: disable=C0114
from ..function_focus import ValueProducer


class Mod(ValueProducer):
    """takes the modulus of numbers"""

    def check_valid(self) -> None:
        self.validate_two_args()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        child = self.children[0]
        siblings = child.commas_to_list()
        ret = 0
        v = siblings[0].to_value(skip=skip)
        m = siblings[1].to_value(skip=skip)
        ret = float(v) % float(m)
        ret = round(ret, 2)
        self.value = ret

    def _decide_match(self, skip=None) -> None:
        self.match = self._noop_match()
