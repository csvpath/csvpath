# pylint: disable=C0114
from csvpath.matching.productions import Term, Variable, Header
from csvpath.matching.functions.function import Function
from csvpath.matching.functions.types.decimal import Decimal
from csvpath.matching.functions.types.boolean import Boolean
from csvpath.matching.functions.types.datef import Date
from csvpath.matching.functions.types.string import String
from csvpath.matching.functions.types.nonef import Nonef
from csvpath.matching.functions.types.email import Email
from csvpath.matching.functions.types.url import Url
from ..function_focus import ValueProducer
from ..args import Args


class Datatype(ValueProducer):
    def check_valid(self) -> None:
        # self.value_qualifiers.append("notnone")
        self.description = [
            self._cap_name(),
            """datatype() returns the best fitting type for a header value on a given line.
              String is considered the least specific type, meaning that a type is only
              considered a string if all other types do not match. For example, "" is
              considered a none() match and "false" is considered a boolean() match.
            """,
        ]
        self.args = Args(matchable=self)
        a = self.args.argset(1)
        a.arg(name="header of value", types=[Variable, Header, Function], actuals=[str])
        self.args.validate(self.siblings())
        super().check_valid()

    def _decide_match(self, skip=None) -> None:
        # self.to_value(skip=skip)
        self.match = True

    def _produce_value(self, skip=None) -> None:
        # c = self._child_one()
        v = self._value_one(skip=skip)
        t = "unknown"

        if Decimal._is_match(name="decimal", value=v, strict=True)[0]:
            t = "decimal"
        elif Decimal._is_match(name="integer", value=v, strict=True)[0]:
            t = "integer"
        elif Boolean._is_match(v)[0]:
            t = "boolean"
        elif Date._is_match(is_datetime=True, value=v, strict=True):
            t = "datetime"
        elif Date._is_match(is_datetime=False, value=v, strict=True):
            t = "date"
        elif Nonef._is_match(v):
            t = "none"
        elif Url._is_match(v):
            t = "url"
        elif Email._is_match(v):
            t = "email"
        elif String._is_match(v):
            t = "string"
        self.value = t
