# pylint: disable=C0114
from typing import Any
from csvpath.matching.productions import Equality, Header, Variable
from csvpath.matching.util.exceptions import ChildrenException
from csvpath.matching.util.expression_utility import ExpressionUtility
from ..function_focus import ValueProducer
from ..args import Args


class EmptyStack(ValueProducer):
    """collects empty header names and/or indexes in a stack var."""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        self.args.argset(0)
        self.args.argset().arg(types=[None, Variable, Header], actuals=[None, Any])
        self.args.validate(self.siblings())
        super().check_valid()  # pragma: no cover

    def _produce_value(self, skip=None) -> None:
        if len(self.children) == 0:
            self._do_all()
        elif len(self.children) == 1 and isinstance(self.children[0], Equality):
            self._do_some()
        else:
            self._do_one()

    def _decide_match(self, skip=None) -> None:
        st = self.to_value(skip=skip)
        self.match = st and len(st) != 0

    def _do_all(self, skip=None):
        self.value = []
        ml = len(self.matcher.line)
        for i, h in enumerate(self.matcher.csvpath.headers):
            if ml > i:
                if ExpressionUtility.is_empty(self.matcher.line[i]):
                    self.value.append(h)
            else:
                self.value.append(h)

    def _do_some(self, skip=None):
        siblings = self.children[0].commas_to_list()
        self.value = []
        for s in siblings:
            v = s.to_value(skip=skip)
            b = ExpressionUtility.is_empty(v)
            if b:
                self.value.append(s.name)

    def _do_one(self, child, skip=None):
        v = child.to_value(skip=skip)
        self.value = [ExpressionUtility.is_empty(v)]
