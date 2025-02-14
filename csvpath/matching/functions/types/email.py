# pylint: disable=C0114
from email_validator import validate_email, EmailNotValidError
from csvpath.matching.productions import Term, Header, Variable, Reference
from csvpath.matching.functions.function import Function
from ..args import Args
from .type import Type


class Email(Type):
    def check_valid(self) -> None:
        self.match_qualifiers.append("notnone")
        self.value_qualifiers.append("notnone")
        self.description = [
            self._cap_name(),
            "A line() schema type indicating that the value it represents must be an email",
        ]
        #
        #
        #
        self.args = Args(matchable=self)
        a = self.args.argset(1)
        a.arg(
            name="address",
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
        if (val is None or f"{val}".strip() == "") and self.notnone:
            self.match = False
        elif val is None or f"{val}".strip() == "":
            self.match = True
        else:
            try:
                validate_email(val, check_deliverability=False)
                self.match = True
            except EmailNotValidError:
                self.match = False
