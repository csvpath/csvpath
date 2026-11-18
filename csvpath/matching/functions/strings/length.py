# pylint: disable=C0114
from typing import Any
from ..function_focus import ValueProducer
from csvpath.matching.util.exceptions import MatchComponentException
from csvpath.matching.productions import Term, Variable, Header, Reference
from ..function import Function
from ..args import Args


class Length(ValueProducer):
    """returns the length of a string"""

    def check_valid(self) -> None:
        self.description = [
            self.wrap(
                """\
                   Returns the length of a string.
                """
            ),
        ]
        self.args = Args(matchable=self)
        a = self.args.argset(1)
        a.arg(
            name="get length",
            types=[Term, Variable, Header, Function, Reference],
            actuals=[None, str, self.args.EMPTY_STRING],
        )
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        val = self.children[0].to_value(skip=skip)
        ret = 0
        if val:
            ret = len(f"{val}")
        self.value = ret

    def _decide_match(self, skip=None) -> None:
        self.match = self.to_value(skip=skip) > 0


class MinMaxLength(ValueProducer):  # pylint: disable=C0115
    def check_valid(self) -> None:
        self.description = [
            self.wrap(
                """\
                    too_long() and min_length() are True when the value has at
                    least the given number of characters. too_short() and
                    max_length() are True when it has at most that number.
                """
            ),
            self.wrap(
                """\
                    Read too_long(#name, 5) as "a value that is 5 characters is
                    too long for this field": the value must be 4 or fewer
                    characters to pass. too_short(#name, 5) is True for a value
                    of 5 or fewer characters.
                """
            ),
        ]
        self.args = Args(matchable=self)
        a = self.args.argset(2)
        a.arg(
            types=[Term, Variable, Header, Function, Reference],
            actuals=[str, self.args.EMPTY_STRING],
        )
        a.arg(types=[Term], actuals=[int])
        self.args.validate(self.siblings())
        super().check_valid()

    #
    # this was a to_value() override, which skipped the standard to_value():
    # onmatch was ignored and a None reached len() as a raw TypeError.
    # _produce_value() gets both from Function.to_value().
    #
    def _produce_value(self, skip=None) -> None:
        value = self.children[0].left.to_value(skip=skip)
        length = self.children[0].right.to_value(skip=skip)
        length = int(length)
        if self.name in ["min_length", "too_long"]:
            self.value = len(value) >= length
        elif self.name in ["max_length", "too_short"]:
            self.value = len(value) <= length

    def _decide_match(self, skip=None) -> None:
        v = self.to_value(skip=skip)
        self.match = v
