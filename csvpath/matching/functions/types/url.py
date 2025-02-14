# pylint: disable=C0114
import validators
from csvpath.matching.productions import Term, Header, Variable, Reference
from csvpath.matching.functions.function import Function
from ..args import Args
from .type import Type


class Url(Type):
    def check_valid(self) -> None:
        self.match_qualifiers.append("notnone")
        self.value_qualifiers.append("notnone")
        self.description = [
            self._cap_name(),
            "A line() schema type indicating that the value it represents must be an URL",
        ]
        self.args = Args(matchable=self)
        a = self.args.argset(1)
        a.arg(
            name="url",
            types=[Header, Variable, Reference, Function],
            actuals=[str, None, self.args.EMPTY_STRING],
        )
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.matches(skip=skip)
        self.value = self.match

    def _decide_match(self, skip=None) -> None:
        val = self._value_one()
        val = f"{val}".strip()
        if val == "" and self.notnone:
            self.match = False
            return
        elif val == "":
            self.match = True
            return
        self.match = validators.url(val) is True
