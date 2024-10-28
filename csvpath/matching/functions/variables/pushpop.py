# pylint: disable=C0114
from typing import Any
from csvpath.matching.util.expression_utility import ExpressionUtility
from csvpath.matching.productions import Variable, Header, Term, Reference
from ..function import Function
from ..function_focus import SideEffect, ValueProducer
from ..args import Args


class Push(SideEffect):
    """pushes values onto a stack variable"""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset(2)
        a.arg(types=[Term, Variable, Header, Function, Reference], actuals=[str])
        a.arg(types=[Term, Variable, Header, Function, Reference], actuals=[None, Any])
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self._apply_default_value()

    def _decide_match(self, skip=None) -> None:
        eq = self.children[0]
        k = eq.left.to_value(skip=skip)
        v = eq.right.to_value(skip=skip)
        stack = self.matcher.get_variable(k, set_if_none=[])
        if stack is None or isinstance(stack, tuple):
            self.matcher.csvpath.logger.warning(  # pragma: no cover
                "Push cannot add to the stack. The run may be ending."
            )
        elif (
            self.has_qualifier("distinct") or self.name == "push_distinct"
        ) and v in stack:
            pass
        elif self.notnone and ExpressionUtility.is_empty(v):
            pass
        else:
            stack.append(v)
        self.match = self.default_match()


class PushDistinct(Push):
    """pushes only distinct values to a stack variable"""

    def check_valid(self) -> None:  # pylint: disable=W0246
        # re: W0246: Matchable handles the children's validity
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:
        self.add_qualifier("distinct")
        return super().to_value(skip=skip)


class Pop(ValueProducer):
    """poppes the top value off a stack variable"""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset(1)
        a.arg(types=[Variable, Header, Function, Reference, Term], actuals=[None, str])
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        k = self.children[0].to_value(skip=skip)
        stack = self.matcher.get_variable(k, set_if_none=[])
        if len(stack) > 0:
            self.value = stack[len(stack) - 1]
            stack = stack[0 : len(stack) - 2]
            self.matcher.set_variable(k, value=stack)

    def _decide_match(self, skip=None) -> None:
        v = self.to_value(skip=skip)
        if self.asbool:
            self.match = ExpressionUtility.asbool(v)
        else:
            self.match = self.default_match()  # pragma: no cover


class Stack(SideEffect):
    """returns a stack variable"""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset(1)
        a.arg(types=[Variable, Header, Function, Reference, Term], actuals=[str])
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        k = self.children[0].to_value(skip=skip)
        stack = self.matcher.get_variable(k, set_if_none=[])
        if not isinstance(stack, list):
            thelist = []
            thelist.append(stack)
            stack = thelist
            self.matcher.set_variable(k, value=stack)
        self.value = stack

    def _decide_match(self, skip=None) -> None:
        self.match = self.default_match()  # pragma: no cover


class Peek(ValueProducer):
    """gets the value of the top item in a stack variable"""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset(2)
        a.arg(types=[Term, Variable, Header, Function, Reference], actuals=[str])
        a.arg(types=[Term], actuals=[int])
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        eq = self.children[0]
        k = eq.left.to_value(skip=skip)
        v = eq.right.to_value(skip=skip)
        v = int(v)
        stack = self.matcher.get_variable(k, set_if_none=[])
        if v < len(stack):
            self.value = stack[v]

    def _decide_match(self, skip=None) -> None:
        v = self.to_value(skip=skip)
        if self.asbool:
            self.match = ExpressionUtility.asbool(v)
        else:
            self.match = self.default_match()  # pragma: no cover


class PeekSize(ValueProducer):
    """gets the number of items in a stack variable"""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset(1)
        a.arg(types=[Variable, Header, Function, Reference, Term], actuals=[str])
        self.args.validate(self.siblings_or_equality())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        k = self.children[0].to_value(skip=skip)
        stack = self.matcher.get_variable(k, set_if_none=[])
        self.value = len(stack)

    def matches(self, *, skip=None) -> bool:
        self.matches = self.default_match()  # pragma: no cover
