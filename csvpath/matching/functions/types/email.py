# pylint: disable=C0114
from email_validator import validate_email, EmailNotValidError
from csvpath.matching.productions import Header, Variable, Reference
from csvpath.matching.functions.function import Function
from ..args import Args
from .type import Type


class Email(Type):
    def check_valid(self) -> None:
        self.match_qualifiers.append("notnone")
        self.match_qualifiers.append("distinct")
        self.value_qualifiers.append("notnone")
        self.description = [
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
        self._distinct_if(skip=skip)
        if (val is None or f"{val}".strip() == "") and self.notnone:
            self.match = False
        elif val is None or f"{val}".strip() == "":
            self.match = True
        else:
            self.match = Email._is_match(val)

    @classmethod
    def _is_match(cls, value: str) -> bool:
        if value is None:
            return False
        try:
            validate_email(value, check_deliverability=False)
            return True
        #
        # we need to catch typeerror here, because datatype is
        # using this method expecting that it always returns.
        # we catch TypeError and ValueError in Function to_value
        # and never raise. that is because Args does type and
        # value testing. but here Args doesn't get a chance to
        # help out. this problem highlights a risk. but for now
        # our best bet in the near term is just to start logging
        # those Value and Type errors, if any, rather than
        # assuming they were already handled as Children or Match
        # errors.
        #
        except (TypeError, EmailNotValidError):
            return False
