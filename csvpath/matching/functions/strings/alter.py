# pylint: disable=C0114
from csvpath.matching.productions import Term, Variable, Header, Reference
from csvpath.matching.util.exceptions import ChildrenException
from ..function_focus import ValueProducer
from ..function import Function
from ..args import Args


class Alter(ValueProducer):
    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                   Alters a string by replacing all instances of a substring.
                """
            ),
        ]
        self.args = Args(matchable=self)
        a = self.args.argset(3)
        a.arg(
            name="in",
            types=[Term, Variable, Header, Function, Reference],
            actuals=[str, self.args.EMPTY_STRING, None],
        )
        a.arg(
            name="find",
            types=[Term, Variable, Header, Function, Reference],
            actuals=[str, self.args.EMPTY_STRING, None],
        )
        a.arg(
            name="replace",
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
