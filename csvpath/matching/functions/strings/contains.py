# pylint: disable=C0114
from csvpath.matching.productions import Term, Variable, Header, Reference
from csvpath.matching.util.exceptions import ChildrenException
from ..function_focus import ValueProducer
from ..function import Function
from ..args import Args


class Contains(ValueProducer):
    """returns true if the first string contains the second"""

    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                   Matches if the first string contains the second.
                """
            ),
        ]
        self.args = Args(matchable=self)
        a = self.args.argset(2)
        a.arg(
            name="does this",
            types=[Term, Variable, Header, Function, Reference],
            actuals=[str, self.args.EMPTY_STRING, None],
        )
        #
        # we accept None because we have to function when None is found
        # in the inputs
        #
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
        if self.name == "contains":
            self.value = p > -1
        elif self.name == "find":
            self.value = p
        else:
            raise ChildrenException("Unexpected name: {self.name}")

    def _decide_match(self, skip=None) -> None:
        v = self.to_value(skip=skip)
        if self.name == "contains":
            self.match = v
        else:
            self.match = v > -1
