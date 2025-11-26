# pylint: disable=C0114
from csvpath.matching.productions import Term, Variable, Header, Reference
from csvpath.matching.util.exceptions import ChildrenException
from csvpath.matching.functions.function_focus import ValueProducer
from csvpath.matching.functions.function import Function
from csvpath.matching.functions.args import Args


class Extract(ValueProducer):
    """this is a very slightly modified string checking function. it's only
    purpose is to check that we can load it from this location."""

    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap("""A test custom function"""),
        ]
        self.args = Args(matchable=self)
        a = self.args.argset(2)
        a.arg(
            name="does this",
            types=[Term, Variable, Header, Function, Reference],
            actuals=[str, self.args.EMPTY_STRING, None],
        )
        a.arg(
            name="contain this",
            types=[Term, Variable, Header, Function, Reference],
            actuals=[str, self.args.EMPTY_STRING, None],
        )
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        string = self._value_one(skip=skip)
        if string is None:
            self.value = False if self.name == "contains" else -1
            return
        string = f"{string}"
        s2 = self._value_two(skip=skip)
        if s2 is None:
            self.value = False if self.name == "contains" else -1
            return
        s2 = f"{s2}"
        p = string.find(s2)
        self.value = p > -1

    def _decide_match(self, skip=None) -> None:
        v = self.to_value(skip=skip)
        if self.name == "contains":
            self.match = v
        else:
            self.match = v > -1
