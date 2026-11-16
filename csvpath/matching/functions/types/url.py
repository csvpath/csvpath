# pylint: disable=C0114
import validators
from csvpath.matching.productions import Term, Header, Variable, Reference
from csvpath.matching.util.expression_utility import ExpressionUtility
from csvpath.matching.functions.function import Function
from ..args import Args
from .type import Type


class Url(Type):
    def check_valid(self) -> None:
        self.match_qualifiers.append("notnone")
        self.match_qualifiers.append("distinct")
        self.value_qualifiers.append("notnone")
        self.description = [
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
        val = self._value_one(skip=skip)
        self._distinct_if(skip=skip)
        #
        # None is missing, like "", as in email() and uuid(). this used to
        # stringify first, so None became "None" and failed validation:
        # url(none()) did not match even without notnone.
        #
        if (val is None or f"{val}".strip() == "") and self.notnone:
            self.match = False
        elif val is None or f"{val}".strip() == "":
            self.match = True
        else:
            self.match = Url._is_match(f"{val}".strip())

    @classmethod
    def _is_match(cls, value: str) -> bool:
        if value is None:
            return False
        return validators.url(value) is True
