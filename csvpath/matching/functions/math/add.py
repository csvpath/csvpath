# pylint: disable=C0114

from csvpath.matching.productions import Term, Variable, Header, Reference
from csvpath.matching.util.expression_utility import ExpressionUtility
from csvpath.matching.util.exceptions import MatchException
from ..function_focus import ValueProducer
from ..function import Function
from ..args import Args


class Add(ValueProducer):
    """this class adds numbers"""

    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
            Adds numbers. add() can take any number of int and/or float arguments.
            """
            ),
        ]
        self.args = Args(matchable=self)
        a = self.args.argset()
        a.arg(
            name="add this",
            types=[Term, Variable, Header, Function, Reference],
            actuals=[None, int, float],
        )
        a.arg(
            name="to that",
            types=[Term, Variable, Header, Function, Reference],
            actuals=[None, int, float],
        )
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        child = self.children[0]
        siblings = child.commas_to_list()
        ret = 0
        for sib in siblings:
            v = sib.to_value(skip=skip)
            if ExpressionUtility.is_none(v):
                v = 0
            try:
                ret = float(v) + float(ret)
            except ValueError as e:
                msg = f"{e}"
                self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
                if self.matcher.csvpath.do_i_raise():
                    raise MatchException(msg) from e
        self.value = ret

    def _decide_match(self, skip=None) -> None:
        # we want to_value called so that if we would blow-up in
        # assignment, equality, etc. we still blow-up even though we're not
        # using the sum.
        self.to_value(skip=skip)
        self.match = self.default_match()
