# pylint: disable=C0114
from ..function_focus import ValueProducer


class Strip(ValueProducer):
    """removes whitespace from the beginning and end of a string"""

    def check_valid(self) -> None:
        self.validate_one_arg()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        v = self.children[0].to_value()
        string = f"{v}"
        self.value = string.strip()

    def _decide_match(self, skip=None) -> None:
        self.to_value(skip=skip)  # pragma: no cover
        self.match = self._apply_default_match()  # pragma: no cover
