# pylint: disable=C0114
from csvpath.matching.util.exceptions import ChildrenException
from ..function_focus import ValueProducer


class Substring(ValueProducer):
    """returns a substring of a value from 0 to N.
    unlike Python we do not allow negatives."""

    def check_valid(self) -> None:
        self.validate_two_args()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        i = self._value_two(skip=skip)
        if not isinstance(i, int):
            raise ChildrenException("substring()'s 2nd argument must be a positive int")
        i = int(i)
        if i < 0:
            raise ChildrenException("substring()'s 2nd argument must be a positive int")
        string = self._value_one(skip=skip)
        string = f"{string}"
        if i >= len(string):
            self.value = string
        else:
            self.value = string[0:i]

    def _decide_match(self, skip=None) -> None:
        self.match = self.default_match()
