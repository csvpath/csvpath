# pylint: disable=C0114
from typing import Any
from csvpath.matching.util.exceptions import ChildrenException
from csvpath.matching.util.expression_utility import ExpressionUtility
from ..function_focus import ValueProducer
from csvpath.matching.productions import Term, Matchable
from ..function import Function
from ..args import Args


class Every(ValueProducer):
    """uses the % of values seen to select every N sightings of a
    value. results in a list of counts of values (potentially
    quite expensive) behind the scenes for generating the %.
    since there isn't an intrinsic state we're exposing and the
    values generated are useful, this is a ValueProducer.
    """

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset(2)
        a.arg(types=[Matchable], actuals=[None, Any])
        a.arg(types=[Term], actuals=[int])
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        child = self.children[0]
        tracked_value = child.left.to_value(skip=skip)
        cnt = self.matcher.get_variable(
            self.me(), tracking=tracked_value, set_if_none=0
        )
        cnt += 1
        self.matcher.set_variable(self.me(), tracking=tracked_value, value=cnt)

        every = child.right.to_value(skip=skip)
        every = ExpressionUtility.to_int(every)
        self.value = cnt % every

    def _decide_match(self, skip=None) -> None:
        cnt = self.to_value(skip=skip)
        if cnt == 0:
            self.match = True
        else:
            self.match = False

    def me(self):
        return self.qualifier if self.qualifier is not None else self.get_id(self)
