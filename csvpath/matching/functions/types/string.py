# pylint: disable=C0114
from csvpath.matching.util.exceptions import ChildrenException
from ..function_focus import ValueProducer
from csvpath.matching.productions import Term, Variable, Header, Reference
from csvpath.matching.util.expression_utility import ExpressionUtility
from ..function import Function
from ..args import Args
from .type import Type


class String(Type):
    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset(1)
        a.arg(
            name="header name",
            types=[Term],
            actuals=[str, int],
        )
        # why self.args.EMPTY_STRING? we'll never have an empty string
        # term. if we only allow terms we're only ever pointing to a
        # header. If we allow other types we'll resolve them potentially
        # to the empty string, but that's not what we're doing today.
        a = self.args.argset(3)
        a.arg(
            name="header name",
            types=[Term],
            actuals=[str, int],
        )
        a.arg(name="max value", types=[None, Term], actuals=[int])
        a.arg(name="min value", types=[None, Term], actuals=[int])
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.matches(skip=skip)
        self.value = f"{self._value_one()}" if self.match else None

    def _decide_match(self, skip=None) -> None:
        value = self._value_one(skip=skip)
        value = f"{value}" if value is not None else None
        # resolve the value of the header that our value names
        val = self.resolve_value(skip=skip)
        # our to_value cannot be none because Args
        # our resolved value can be none or '' and
        # we might not accept that
        if val is None and self.notnone:
            self.match = False
        elif val is None:
            self.match = True
        else:
            self._check_length_if(val)

    def _check_length_if(self, value, skip=None) -> None:
        maxlen = self._value_two(skip=skip)
        minlen = self._value_three(skip=skip)
        if minlen is None:
            minlen = 0
        if maxlen is None:
            maxlen = len(value)
        if maxlen < minlen:
            self.raiseChildrenException(
                "Max length ({maxlen}) cannot be less than min length ({minlen})"
            )
        self.match = minlen <= len(value) <= maxlen
