# pylint: disable=C0114
from ..function_focus import ValueProducer


class Upper(ValueProducer):
    """uppercases a string"""

    def check_valid(self) -> None:
        self.validate_one_arg()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        value = self.children[0].to_value(skip=skip)
        self.value = f"{value}".upper()

    def _decide_match(self, skip=None) -> None:
        v = self.to_value(skip=skip)
        self.match = v is not None
