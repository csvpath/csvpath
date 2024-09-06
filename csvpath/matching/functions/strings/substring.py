# pylint: disable=C0114
from csvpath.matching.util.exceptions import ChildrenException
from ..function_focus import ValueProducer


class Substring(ValueProducer):
    """returns a substring of a value from 0 to N"""

    def check_valid(self) -> None:
        self.validate_two_args()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        i = self.children[0].right.to_value(skip=skip)
        if not isinstance(i, int):
            raise ChildrenException("substring()'s 2nd argument must be an int")
        i = int(i)
        string = self.children[0].left.to_value(skip=skip)
        string = f"{string}"
        if i >= len(string):
            self.value = string
        else:
            self.value = string[0:i]

    def _decide_match(self, skip=None) -> None:
        v = self.to_value(skip=skip)
        self.match = v is not None
