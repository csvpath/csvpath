# pylint: disable=C0114
from csvpath.matching.productions import Term, Variable, Header
from ..function_focus import ValueProducer
from ..function import Function


class Lower(ValueProducer):
    """lowercases a string"""

    def check_valid(self) -> None:
        self.validate_one_arg(types=[Term, Variable, Header, Function])
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        value = self.children[0].to_value(skip=skip)
        self.value = f"{value}".lower()

    def _decide_match(self, skip=None) -> None:
        self.to_value(skip=skip)
        self.match = self._noop_match()
