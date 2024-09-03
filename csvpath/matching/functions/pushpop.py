# pylint: disable=C0114
from typing import Any
from .function import Function
from ..util.expression_utility import ExpressionUtility
from ..productions.equality import Equality


class Push(Function):
    """pushes values onto a stack variable"""

    def check_valid(self) -> None:
        self.validate_two_args()
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:
        if skip and self in skip:  # pragma: no cover
            return self._noop_value()
        if self.value is None:
            if not self.onmatch or self.line_matches:
                eq = self.children[0]
                k = eq.left.to_value()
                v = eq.right.to_value()
                stack = self.matcher.get_variable(k, set_if_none=[])
                if self.has_qualifier("distinct") and v in stack:
                    pass
                elif isinstance(stack, tuple):
                    self.matcher.csvpath.logger.warning(
                        "Push cannot add to the stack because it is a tuple. The run may be ending."
                    )
                elif stack is not None:
                    stack.append(v)
                else:
                    self.matcher.csvpath.logger.warning(
                        "Push cannot do its work because no default stack was created. The run may be ending."
                    )
                    # self.matcher.set_variable(
                    #     k, value=stack
                    # )  # technically we don't have to call set because refs
        self.value = True
        return self.value

    def matches(self, *, skip=None) -> bool:
        if skip and self in skip:  # pragma: no cover
            return self._noop_match()
        return self.to_value(skip=skip)


class PushDistinct(Push):
    """pushes only distinct values to a stack variable"""

    def check_valid(self) -> None:
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:
        self.add_qualifier("distinct")
        return super().to_value(skip=skip)


class Pop(Function):
    """poppes the top value off a stack variable"""

    def check_valid(self) -> None:
        self.validate_one_arg()
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:
        if skip and self in skip:  # pragma: no cover
            return self._noop_value()
        if self.value is None:
            k = self.children[0].to_value()
            stack = self.matcher.get_variable(k, set_if_none=[])
            if len(stack) > 0:
                self.value = stack[len(stack) - 1]
                stack = stack[0 : len(stack) - 2]
                self.matcher.set_variable(k, value=stack)
        return self.value

    def matches(self, *, skip=None) -> bool:
        if skip and self in skip:  # pragma: no cover
            return self._noop_match()
        v = self.to_value(skip=skip)
        if self.asbool:
            self.match = ExpressionUtility.asbool(v)
        else:
            self.match = True
        return self.match


class Stack(Function):
    """returns a stack variable"""

    def check_valid(self) -> None:
        self.validate_one_arg()
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:
        if skip and self in skip:  # pragma: no cover
            return self._noop_value()
        if self.value is None:
            k = self.children[0].to_value()
            stack = self.matcher.get_variable(k, set_if_none=[])
            if not isinstance(stack, list):
                thelist = []
                stack = thelist.append(stack)
                self.matcher.set_variable(k, value=thelist)
            self.value = stack
        return self.value

    def matches(self, *, skip=None) -> bool:
        return self._noop_match()


class Peek(Function):
    """gets the value of the top item in a stack variable"""

    def check_valid(self) -> None:
        self.validate_two_args()
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:
        if skip and self in skip:  # pragma: no cover
            return self._noop_value()
        if self.value is None:
            eq = self.children[0]
            k = eq.left.to_value()
            v = eq.right.to_value()
            v = int(v)
            stack = self.matcher.get_variable(k, set_if_none=[])
            if v < len(stack):
                self.value = stack[v]
        return self.value

    def matches(self, *, skip=None) -> bool:
        if skip and self in skip:  # pragma: no cover
            return self._noop_match()
        v = self.to_value(skip=skip)
        if self.asbool:
            self.match = ExpressionUtility.asbool(v)
        else:
            self.match = True
        return self.match


class PeekSize(Function):
    """gets the number of items in a stack variable"""

    def check_valid(self) -> None:
        self.validate_one_arg()
        super().check_valid()

    def to_value(self, *, skip=None) -> Any:
        if skip and self in skip:  # pragma: no cover
            return self._noop_value()
        if self.value is None:
            k = self.children[0].to_value()
            stack = self.matcher.get_variable(k, set_if_none=[])
            self.value = len(stack)
        return self.value

    def matches(self, *, skip=None) -> bool:
        return self._noop_match()  # pragma: no cover
