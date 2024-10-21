# pylint: disable=C0114
import datetime
from ..function_focus import ValueProducer
from ..args import Args
from ..function import Function
from csvpath.matching.productions import Header, Variable, Reference, Term
from csvpath.matching.util.expression_utility import ExpressionUtility


class Date(ValueProducer):
    """parses a date from a string"""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset(1)
        a.arg(
            types=[Term, Header, Variable, Function, Reference],
            actuals=[datetime.datetime, datetime.date],
        )
        a = self.args.argset(2)
        a.arg(types=[Term, Variable, Header, Function, Reference], actuals=[str])
        a.arg(types=[Term, Variable, Header, Function, Reference], actuals=[str])
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        v = self._value_one(skip=skip)
        v = f"{v}".strip()
        fmt = self._value_two(skip=skip)
        if fmt:
            fmt = f"{fmt}".strip()
            d = datetime.datetime.strptime(v, fmt)
        else:
            d = ExpressionUtility.to_datetime(v)
        if isinstance(d, datetime.datetime) and not self.name == "datetime":
            d = d.date()
        self.value = d

    def _decide_match(self, skip=None) -> None:
        self.match = self.to_value(skip=skip) is not None  # pragma: no cover
