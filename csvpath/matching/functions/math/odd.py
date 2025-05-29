# pylint: disable=C0114
from typing import Any
from csvpath.matching.productions import Variable, Header, Reference, Equality
from csvpath.matching.util.expression_utility import ExpressionUtility
from ..function import Function
from ..function_focus import MatchDecider
from ..args import Args


class Odd(MatchDecider):
    """returns true if n%2==0"""

    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                f"""\
                    Checks a contained value to see if it is {self.name}.
                """
            ),
        ]

        self.args = Args(matchable=self)
        a = self.args.argset(1)
        a.arg(
            name="check this",
            types=[Variable, Header, Function, Reference, Equality],
            actuals=[None, int],
        )
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:
        v = self._value_one(skip=skip)
        i = ExpressionUtility.to_int(v)
        if self.name == "odd":
            self.match = i % 2 == 1
        elif self.name == "even":
            self.match = i % 2 == 0
