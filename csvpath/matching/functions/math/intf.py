# pylint: disable=C0114
from csvpath.matching.util.expression_utility import ExpressionUtility
from csvpath.matching.productions import Term, Variable, Header
from ..function import Function
from ..function_focus import ValueProducer
from ..args import Args


class Int(ValueProducer):
    """attempts to convert a value to an int"""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset(1)
        a.arg(types=[Term, Variable, Header, Function], actuals=[None, int, float])
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        i = self._value_one(skip=skip)
        if i is None:
            self.value = None
        else:
            try:
                self.value = ExpressionUtility.to_int(i)
            except ValueError as e:
                self.my_expression.handle_error(e)

    def _decide_match(self, skip=None) -> None:
        self.match = self.default_match()  # pragma: no cover


class Float(ValueProducer):
    """attempts to convert a value to a float"""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset(1)
        a.arg(types=[Term, Variable, Header, Function], actuals=[None, float, int])
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        i = self._value_one(skip=skip)
        if i is None:
            self.value = None
        else:
            try:
                self.value = ExpressionUtility.to_float(i)
            except ValueError as e:
                self.my_expression.handle_error(e)

    def _decide_match(self, skip=None) -> None:
        self.match = self.default_match()  # pragma: no cover


class Num(ValueProducer):
    """parses a string or stringified object to a float, if possible,
    ints and bools stay ints"""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset(1)
        a.arg(
            types=[Term, Variable, Header, Function],
            actuals=[None, int, float, bool],
        )
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        value = self._value_one(skip=skip)
        try:
            if isinstance(value, int):
                self.value = int(value)
            elif isinstance(value, float):
                self.value = value
            else:
                self.value = ExpressionUtility.to_float(value)
        except ValueError as e:
            self.my_expression.handle_error(e)

    def _decide_match(self, skip=None) -> None:
        self.match = self.default_match()
