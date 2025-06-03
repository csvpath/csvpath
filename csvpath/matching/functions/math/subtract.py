# pylint: disable=C0114
from ..function_focus import ValueProducer
from csvpath.matching.productions import Term, Variable, Header, Reference, Equality
from csvpath.matching.util.expression_utility import ExpressionUtility
from ..function import Function
from ..args import Args


class Subtract(ValueProducer):
    """subtracts numbers"""

    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            f"{self.name}() subtracts two or more numbers.",
            """ When there is only one argument, the number is flipped from positive
                to negative or negative to positive.
            """,
        ]
        self.aliases = ["subtract", "minus"]
        self.args = Args(matchable=self)
        a = self.args.argset()
        a.arg(
            name="term",
            types=[Term, Header, Reference, Variable, Function],
            actuals=[int, float],
        )
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        child = self.children[0]
        if isinstance(child, Equality):
            self.value = self._do_sub(child, skip=skip)
        else:
            v = child.to_value()
            #
            # this will not fail. args already checked.
            #
            v = ExpressionUtility.to_float(v)
            self.value = v * -1

    def _do_sub(self, child, skip=None):
        siblings = child.commas_to_list()
        ret = 0
        for i, sib in enumerate(siblings):
            v = sib.to_value(skip=skip)
            if i == 0:
                ret = v
            else:
                ret = float(ret) - float(v)
        return ret

    def _decide_match(self, skip=None) -> None:
        # we want to_value called so that if we would blow-up in
        # assignment, equality, etc. we still blow-up even though we're not
        # using the difference.
        self.to_value(skip=skip)
        self.match = self.default_match()
