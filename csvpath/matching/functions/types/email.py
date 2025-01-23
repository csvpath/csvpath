# pylint: disable=C0114
from email_validator import validate_email, EmailNotValidError
from csvpath.matching.productions import Term, Header, Variable, Reference
from csvpath.matching.functions.function import Function
from ..args import Args
from .type import Type


class Email(Type):
    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset(1)
        a.arg(
            name="header name",
            types=[Term],
            actuals=[str],
        )
        a = self.args.argset(1)
        a.arg(
            name="the value found",
            types=[Header, Variable, Reference, Function],
            actuals=[str, None, self.args.EMPTY_STRING],
        )
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.matches(skip=skip)
        self.value = self.match
        """
        if isinstance(self._child_one(), Term):
            self.value = f"{self.resolve_value(skip=skip)}"
        else:
            self.value = f"{self._value_one()}" if self.match else None
        """

    def _decide_match(self, skip=None) -> None:
        val = None
        if isinstance(self._child_one(), Term):
            val = self.resolve_value(skip=skip)
        else:
            val = self._value_one()

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
