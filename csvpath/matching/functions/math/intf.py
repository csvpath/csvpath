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


"""
class Num(ValueProducer):
    ""parses a string or stringified object to a float, if possible,
    ints and bools stay ints""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset(1)
        a.arg(
            types=[Term, Variable, Header, Function], actuals=[None, int, float, bool]
        )
        a = self.args.argset(5)
        a.arg(types=[Term, Variable, Header, Function], actuals=[None, int, float])
        a.arg(types=[Term, Variable, Header, Function], actuals=[int])
        a.arg(types=[None, Term, Variable, Header, Function], actuals=[int])
        a.arg(types=[None, Term, Variable, Header, Function], actuals=[int])
        a.arg(types=[None, Term, Variable, Header, Function], actuals=[int])
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
        ""
        (value, max digits before decimal, min digits before decimal, max places, min places)
            max of -1 means we don't care
            min of -1 means 0, or use -1, we don't care

        ""
        val = self._value_one()
        if not ExpressionUtility.is_one_of(val, (int, float)):
            self.match = False
            return
        else:
            self.match = True

        dmax = self._value_two()
        if dmax is None:
            dmax = -1
        else:
            dmax = ExpressionUtility.to_int(dmax)

        dmin = self._value_three()
        dmin = ExpressionUtility.to_int(dmin) or 0

        dplaces_max = self._value_four()
        if dplaces_max is None:
            dplaces_max = -1
        else:
            dplaces_max = ExpressionUtility.to_int(dplaces_max)

        dplaces_min = self._value_five()
        dplaces_min = ExpressionUtility.to_int(dplaces_min) or 0

        s = f"{val}"
        d = ""
        si = s.find(".")
        if si > -1:
            d = s[si + 1 :]
            s = s[0:si]
        if dmax > -1 and dmin == dmax:
            self.match = len(s) == dmax
        elif dmax > -1 and dmin > 0:
            self.match = dmin <= len(s) <= dmax
        elif dmax > -1 and dmin == -1:
            self.match = dmax >= len(s)
        elif dmax == -1 and dmin > -1:
            self.match = len(s) >= dmin
        if self.match and dplaces_max > -1 and dplaces_min == dplaces_max:
            self.match = len(d) == dplaces_max
        elif self.match and dplaces_max > -1 and dplaces_min in [0, -1]:
            self.match = 0 <= len(d) <= dplaces_max
        elif self.match and dplaces_max == -1 and dplaces_min > -1:
            self.match = len(d) >= dplaces_min
"""
