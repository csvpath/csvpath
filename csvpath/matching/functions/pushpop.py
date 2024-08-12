from typing import Any
from .function import Function, ChildrenException
from ..expression_utility import ExpressionUtility
from ..productions.equality import Equality


class Push(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()
        if len(self.children) != 1:
            raise ChildrenException("Push function must have 1 equality child")
        if not isinstance(self.children[0], Equality) or self.children[0].op != ",":
            raise ChildrenException(
                "Push function must have 1 equality child with the ',' between 2 values"
            )

        if self.value is None:
            eq = self.children[0]
            k = eq.left.to_value()
            v = eq.right.to_value()
            stack = self.matcher.get_variable(k, set_if_none=[])
            if self.has_qualifier("distinct") and v in stack:
                pass
            else:
                stack.append(v)
            self.matcher.set_variable(
                k, value=stack
            )  # technically we don't have to call set becauses refs
        self.value = True
        return self.value

    def matches(self, *, skip=[]) -> bool:
        if self in skip:  # pragma: no cover
            return self._noop_match()
        return self.to_value(skip=skip)


class PushDistinct(Push):
    def to_value(self, *, skip=[]) -> Any:
        self.add_qualifier("distinct")
        return super().to_value(skip=skip)


class Pop(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()
        if len(self.children) != 1:
            raise ChildrenException(
                "Pop function must have 1 child giving the name of the variable"
            )
        if self.value is None:
            k = self.children[0].to_value()
            stack = self.matcher.get_variable(k, set_if_none=[])
            if len(stack) > 0:
                self.value = stack[len(stack) - 1]
                stack = stack[0 : len(stack) - 2]
                self.matcher.set_variable(k, value=stack)
        return self.value

    def matches(self, *, skip=[]) -> bool:
        if self in skip:  # pragma: no cover
            return self._noop_match()
        v = self.to_value(skip=skip)
        if self.asbool:
            self.match = ExpressionUtility.asbool(v)
        else:
            self.match = True
        return self.match


class Stack(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()
        if len(self.children) != 1:
            raise ChildrenException(
                "Stack function must have 1 child giving the name of the variable"
            )
        if self.value is None:
            k = self.children[0].to_value()
            stack = self.matcher.get_variable(k, set_if_none=[])
            if not isinstance(stack, list):
                thelist = []
                stack = thelist.append(stack)
                self.matcher.set_variable(k, value=thelist)
            self.value = stack
        return self.value

    def matches(self, *, skip=[]) -> bool:
        return self._noop_match()


class Peek(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()

        if (
            len(self.children) != 1
            or not isinstance(self.children[0], Equality)
            or self.children[0].op != ","
        ):
            raise ChildrenException(
                "Percent function must have 1 equality child with the ',' between 2 values"
            )
        if self.value is None:
            eq = self.children[0]
            k = eq.left.to_value()
            v = eq.right.to_value()
            v = int(v)
            stack = self.matcher.get_variable(k, set_if_none=[])
            if v < len(stack):
                self.value = stack[v]

        return self.value

    def matches(self, *, skip=[]) -> bool:
        if self in skip:  # pragma: no cover
            return self._noop_match()
        v = self.to_value(skip=skip)
        if self.asbool:
            self.match = ExpressionUtility.asbool(v)
        else:
            self.match = True
        return self.match


class PeekSize(Function):
    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()

        if len(self.children) != 1:
            raise ChildrenException(
                "Percent function must have 1 child naming the variable"
            )
        if self.value is None:
            k = self.children[0].to_value()

            stack = self.matcher.get_variable(k, set_if_none=[])
            self.value = len(stack)

        return self.value

    def matches(self, *, skip=[]) -> bool:
        return self._noop_match()  # pragma: no cover
