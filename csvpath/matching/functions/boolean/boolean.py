# pylint: disable=C0114
from csvpath.matching.util.expression_utility import ExpressionUtility
from csvpath.matching.util.exceptions import DataException
from csvpath.matching.productions import Term, Variable, Header
from ..function import Function
from ..function_focus import ValueProducer
from ..args import Args


class Boolean(ValueProducer):
    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset(1)
        a.arg(types=[Term, Variable, Header, Function], actuals=[None, bool])
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        i = self._value_one(skip=skip)
        if i is None:
            self.value = None
        else:
            self.value = ExpressionUtility.to_bool(i)

    def _decide_match(self, skip=None) -> None:
        # we need to make sure a value is produced so that we see
        # any errors. when we stand alone we're just checking our
        # boolean-iness. when we're producing a value we're checking
        # boolean-iness and casting and raising errors.
        self.to_value(skip=skip)
        self.match = self.default_match()  # pragma: no cover
