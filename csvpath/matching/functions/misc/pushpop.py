# pylint: disable=C0114
from typing import Any
from csvpath.matching.util.expression_utility import ExpressionUtility
from ..function_focus import SideEffect, ValueProducer


class Push(SideEffect):
    """pushes values onto a stack variable"""

    def check_valid(self) -> None:
        self.validate_two_args()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        eq = self.children[0]
        k = eq.left.to_value(skip=skip)
        v = eq.right.to_value(skip=skip)
        stack = self.matcher.get_variable(k, set_if_none=[])
        if self.has_qualifier("distinct") and v in stack:
            pass
        elif isinstance(stack, tuple):
            self.matcher.csvpath.logger.warning(  # pragma: no cover
                "Push cannot add to the stack because it is a tuple. The run may be ending."
            )
        elif stack is not None:
            stack.append(v)
        else:
            self.matcher.csvpath.logger.warning(  # pragma: no cover
                "No default stack was created. Run may be ending."
            )
        self.value = True

    def _decide_match(self, skip=None) -> None:
        self.to_value(skip=skip)
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
        self.validate_one_arg()
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
            self.match = self._apply_default_match()  # pragma: no cover


class Stack(SideEffect):
    """returns a stack variable"""

    def check_valid(self) -> None:
        self.validate_one_arg()
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
        self.match = self._apply_default_match()  # pragma: no cover


class Peek(ValueProducer):
    """gets the value of the top item in a stack variable"""

    def check_valid(self) -> None:
        self.validate_two_args()
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
            self.match = self._apply_default_match()  # pragma: no cover


class PeekSize(ValueProducer):
    """gets the number of items in a stack variable"""

    def check_valid(self) -> None:
        self.validate_one_arg()
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        k = self.children[0].to_value(skip=skip)
        stack = self.matcher.get_variable(k, set_if_none=[])
        self.value = len(stack)

    def matches(self, *, skip=None) -> bool:
        self.matches = self._apply_default_match()  # pragma: no cover
