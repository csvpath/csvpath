# pylint: disable=C0114
from csvpath.matching.util.exceptions import ChildrenException
from ..function_focus import ValueProducer
from csvpath.matching.productions import Term, Variable, Header, Reference
from ..function import Function
from ..args import Args


class String(ValueProducer):
    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset(1)
        a.arg(
            name="header name",
            types=[Term],
            actuals=[str, int, self.args.EMPTY_STRING],
        )
        a = self.args.argset(3)
        a.arg(
            name="header name",
            types=[Term],
            actuals=[str, int, self.args.EMPTY_STRING],
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
        if value is None:
            self.match = False
        else:
            maxlen = self._value_two(skip=skip)
            minlen = self._value_three(skip=skip)
            if minlen is None:
                minlen = 0
            if maxlen is None:
                maxlen = len(value)
            self.match = minlen <= len(value) <= maxlen
