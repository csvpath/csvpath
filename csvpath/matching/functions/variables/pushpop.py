# pylint: disable=C0114
from typing import Any
from csvpath.matching.util.expression_utility import ExpressionUtility
from csvpath.matching.productions import Variable, Header, Term, Reference
from csvpath.matching.util.exceptions import MatchException
from ..function import Function
from ..function_focus import SideEffect, ValueProducer
from ..args import Args


class Push(SideEffect):
    """pushes values onto a stack variable"""

    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                Appends a value to a stack variable. The stack is created if not found.

                If the distinct qualifier is used, the value to be pushed is ignored
                if it is already present in the stack. Adding the notnone qualifier
                prevents push() from adding a None to the stack.
            """
            ),
        ]
        self.match_qualifiers.append("distinct")
        self.match_qualifiers.append("notnone")
        self.match_qualifiers.append("skipnone")

        self.args = Args(matchable=self)
        a = self.args.argset(1)
        a.arg(
            name="new stack name",
            types=[Term],
            actuals=[str],
        )
        a = self.args.argset(2)
        a.arg(
            name="stack name",
            types=[Term, Variable, Header, Function, Reference],
            actuals=[str, list],
        )
        a.arg(
            name="push this",
            types=[Term, Variable, Header, Function, Reference],
            actuals=[None, Any],
        )
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self._apply_default_value()

    def _decide_match(self, skip=None) -> None:
        sibs = self.siblings()
        k = sibs[0].to_value(skip=skip)
        if len(sibs) == 1:
            v = self.matcher.get_variable(k, set_if_none=[])
            if not isinstance(v, (list, tuple)):
                msg = f"Variable {k} must be a stack variable"
                self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
                if self.matcher.csvpath.do_i_raise():
                    raise MatchException(msg)
            self.match = self.default_match()
            return
        v = sibs[1].to_value(skip=skip)
        stack = None
        if isinstance(k, list):
            stack = k
        else:
            stack = self.matcher.get_variable(k, set_if_none=[])
        #
        # make sure we have a usable stack var
        #
        if stack is None or isinstance(stack, tuple):
            self.matcher.csvpath.logger.warning(  # pragma: no cover
                "Push cannot add to the stack. The run may be ending."
            )
            self.match = self.default_match()
            return
        elif not isinstance(stack, list):
            msg = f"Variable {k} must be a stack variable"
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
            if self.matcher.csvpath.do_i_raise():
                raise MatchException(msg)
            else:
                self.match = self.default_match()
                return
        #
        # do the push
        #
        if (self.distinct or self.name == "push_distinct") and v in stack:
            pass
        elif self.skipnone and ExpressionUtility.is_empty(v):
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
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                Removes and returns the last value added to a stack variable.
                The stack is created if not found.
            """
            ),
        ]
        self.match_qualifiers.append("asbool")
        self.args = Args(matchable=self)
        a = self.args.argset(1)
        a.arg(
            name="stack name",
            types=[Variable, Header, Function, Reference, Term],
            actuals=[None, str],
        )
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        k = self.children[0].to_value(skip=skip)
        stack = self.matcher.get_variable(k, set_if_none=[])
        if len(stack) > 0:
            self.value = None if stack == [] else stack[len(stack) - 1]
            stack = [] if stack == [] else stack[0 : len(stack) - 2]
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
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                Returns a stack variable.
                The stack is created if not found.
            """
            ),
        ]
        self.args = Args(matchable=self)
        a = self.args.argset(1)
        a.arg(
            name="stack name",
            types=[Variable, Header, Function, Reference, Term],
            actuals=[str],
        )
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
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                Returns a value at a stack variable index, but does not remove it.

                The stack is created if not found.
            """
            ),
        ]
        self.match_qualifiers.append("asbool")
        self.args = Args(matchable=self)
        a = self.args.argset(2)
        a.arg(
            name="stack name",
            types=[Term, Variable, Header, Function, Reference],
            actuals=[str],
        )
        a.arg(name="index", types=[Term], actuals=[int])
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        eq = self.children[0]
        k = eq.left.to_value(skip=skip)
        v = eq.right.to_value(skip=skip)
        if v is None:
            v = -1
        else:
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
        self.value_qualifiers.append("notnone")
        self.description = [
            self._cap_name(),
            self.wrap(
                """\
                Returns number of values in a stack variable.

                Unless the notnone qualifier is present, the stack is created if not found.
            """
            ),
        ]
        self.aliases = ["peek_size", "size"]
        self.args = Args(matchable=self)
        a = self.args.argset(1)
        a.arg(
            name="stack name",
            types=[Variable, Header, Function, Reference, Term],
            actuals=[str],
        )
        a = self.args.argset(1)
        a.arg(
            name="stack",
            types=[Variable, Function, Reference],
            actuals=[list, tuple, None],
        )
        self.args.validate(self.siblings_or_equality())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        k = self.children[0].to_value(skip=skip)
        if k is None and self.notnone is True:
            msg = "Value cannot be empty because notnone is set"
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
            if self.matcher.csvpath.do_i_raise():
                raise MatchException(msg)
            return
        stack = None
        if isinstance(k, str):
            stack = self.matcher.get_variable(k, set_if_none=[])
        elif isinstance(k, (list, tuple)):
            stack = k
        if self.notnone is True and stack is None:
            msg = "A stack name or a stack value is required"
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
            if self.matcher.csvpath.do_i_raise():
                raise MatchException(msg)
            return
        elif stack is None:
            stack = []
        self.value = len(stack)

    def matches(self, *, skip=None) -> bool:
        self.matches = self.default_match()  # pragma: no cover
