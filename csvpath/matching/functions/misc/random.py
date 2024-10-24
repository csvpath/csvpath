# pylint: disable=C0114
from random import randrange
from random import sample
from csvpath.matching.util.exceptions import DataException
from ..function_focus import ValueProducer
from csvpath.matching.productions import Term, Header, Variable
from csvpath.matching.util.expression_utility import ExpressionUtility
from ..function import Function
from ..args import Args


class Random(ValueProducer):
    """returns a random int within a range"""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset(2)
        a.arg(types=[Term, Variable, Header, Function], actuals=[int])
        a.arg(types=[Term, Variable, Header, Function], actuals=[int])
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        lower = self.children[0].left.to_value(skip=skip)
        upper = self.children[0].right.to_value(skip=skip)
        if upper <= lower:
            # correct Args-type / data exception
            raise DataException("Upper must be an int > than the first arg")
        lower = int(lower)
        upper = int(upper)
        # we are inclusive, but randrange is not
        upper += 1
        self.value = randrange(lower, upper, 1)

    def _decide_match(self, skip=None) -> None:
        self.match = self.default_match()  # pragma: no cover


class Shuffle(ValueProducer):
    """returns a random int within a range without duplicates"""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset(0)
        a = self.args.argset(2)
        a.arg(types=[Term, Variable, Header, Function], actuals=[int])
        a.arg(types=[Term, Variable, Header, Function], actuals=[int])
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        order = self.matcher.get_variable(self.first_non_term_qualifier(self.name))
        if order is None:
            lower = self._value_one(skip=skip)
            upper = self._value_two(skip=skip)
            if lower is None:
                lower = 0
            if upper is None:
                upper = self.matcher.csvpath.line_monitor.data_end_line_number
            elif upper <= lower:
                # correct Args-type / data exception
                raise DataException("Upper must be an int > than the first arg")
            lower = ExpressionUtility.to_int(lower)
            upper = ExpressionUtility.to_int(upper)
            order = sample(range(lower, upper), upper - lower)
        elif order == []:
            return
        self.value = order.pop()
        self.matcher.set_variable(self.first_non_term_qualifier(self.name), value=order)

    def _decide_match(self, skip=None) -> None:
        self.match = self.default_match()  # pragma: no cover
