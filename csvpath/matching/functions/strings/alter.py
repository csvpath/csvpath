# pylint: disable=C0114
from csvpath.matching.productions import Term, Variable, Header, Reference
from csvpath.matching.util.exceptions import ChildrenException
from ..function_focus import ValueProducer
from ..function import Function
from ..args import Args


class Alter(ValueProducer):
    """returns true if the first string contains the second"""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset(3)
        a.arg(
            name="string to alter",
            types=[Term, Variable, Header, Function, Reference],
            actuals=[str, self.args.EMPTY_STRING, None],
        )
        a.arg(
            name="find this",
            types=[Term, Variable, Header, Function, Reference],
            actuals=[str, self.args.EMPTY_STRING, None],
        )
        a.arg(
            name="replace with this",
            types=[Term, Variable, Header, Function, Reference],
            actuals=[str, self.args.EMPTY_STRING, None],
        )
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        string = self._value_one(skip=skip)
        if string is None:
            self.value = string
            return
        string = f"{string}"
        find = self._value_two(skip=skip)
        if find is None:
            self.value = string
            return
        replacement = self._value_three(skip=skip)
        if replacement is None:
            self.value = string
            return

        find = f"{find}"
        replacement = f"{replacement}"
        r = string.replace(find, replacement)
        self.value = r

    def _decide_match(self, skip=None) -> None:
        self.to_value(skip=skip)
        self.match = self.default_match()
