# pylint: disable=C0114
from csvpath.matching.productions import Equality, Variable, Term, Header, Matchable
from csvpath.matching.util.expression_utility import ExpressionUtility
from ..function_focus import ValueProducer
from ..function import Function
from ..args import Args


class Min(ValueProducer):
    """matches when its value is the smallest"""

    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                Tracks the minimum value.
            """
            ),
        ]
        self.args = Args(matchable=self)
        a = self.args.argset(1)
        a.arg(
            name="value to compare",
            types=[Variable, Term, Header, Function],
            actuals=[int, float],
        )
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        name = self.first_non_term_qualifier("min")
        v = self._value_one(skip=skip)
        v = ExpressionUtility.ascompariable(v)
        e = self.matcher.get_variable(name)
        if e is None or (v is not None and v < e):
            self.matcher.set_variable(name, value=v)
            e = v
        self.value = e

    def _decide_match(self, skip=None) -> None:
        self.match = self.default_match()  # pragma: no cover


class Max(ValueProducer):
    """matches when its value is the largest"""

    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                Tracks the maximum value.
            """
            ),
        ]
        self.args = Args(matchable=self)
        a = self.args.argset(1)
        a.arg(
            name="value to compare",
            types=[Variable, Term, Header, Function],
            actuals=[int, float],
        )
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        name = self.first_non_term_qualifier("max")
        v = self._value_one(skip=skip)
        v = ExpressionUtility.ascompariable(v)
        e = self.matcher.get_variable(name)
        if e is None or (v is not None and v > e):
            self.matcher.set_variable(name, value=v)
            e = v
        self.value = e

    def _decide_match(self, skip=None) -> None:
        self.match = self.default_match()  # pragma: no cover
