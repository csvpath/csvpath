# pylint: disable=C0114
from csvpath.matching.productions import Equality, Term
from ..function_focus import ValueProducer


class Subtract(ValueProducer):
    """subtracts numbers"""

    def check_valid(self) -> None:
        self.validate_one_or_more_args()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        child = self.children[0]
        if isinstance(child, Term):
            v = child.to_value()
            v = int(v)
            self.value = v * -1
        elif isinstance(child, Equality):
            self.value = self._do_sub(child, skip=skip)

    def _do_sub(self, child, skip=None):
        siblings = child.commas_to_list()
        ret = 0
        for i, sib in enumerate(siblings):
            v = sib.to_value(skip=skip)
            if i == 0:
                ret = v
            else:
                ret = float(ret) - float(v)
        return ret

    def _decide_match(self, skip=None) -> None:
        self.match = self._noop_match()
