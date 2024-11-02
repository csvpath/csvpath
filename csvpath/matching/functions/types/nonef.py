# pylint: disable=C0114
from typing import Any
from ..function_focus import ValueProducer
from csvpath.matching.util.expression_utility import ExpressionUtility
from csvpath.matching.util.exceptions import ChildrenException
from csvpath.matching.productions import Variable, Header, Reference, Term
from csvpath.matching.functions.function import Function
from ..args import Args


class Nonef(ValueProducer):
    """returns None"""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        self.args.argset(0)
        a = self.args.argset(1)
        a.arg(
            name="null check",
            types=[Variable, Header, Function, Reference],
            actuals=[None],
        )
        a = self.args.argset(1)
        a.arg(name="header reference", types=[Term], actuals=[str])
        self.args.validate(self.siblings())
        super().check_valid()

    # def to_value(self, *, skip=None) -> Any:  # pragma: no cover
    def _produce_value(self, skip=None) -> None:
        self.value = None

    def _decide_match(self, *, skip=None) -> None:  # pragma: no cover
        if len(self.children) == 0:
            self.match = True
        if isinstance(self._child_one(), Term):
            v = self._value_one(skip=skip)
            h = self.matcher.get_header_value(self, v)
            self.match = ExpressionUtility.is_none(h)
            if self.match is False:
                msg = self.decorate_error_message(f"'{v}' must be empty")
                self.parent.raise_if(ChildrenException(msg))
        else:
            self.match = ExpressionUtility.is_none(self._value_one(skip=skip))

    def resolve_value(self, skip=None) -> str | None:
        return None


class Blank(ValueProducer):
    """returns True to match, returns its child's value or None. represents any value"""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        self.args.argset(0)
        a = self.args.argset(1)
        a.arg(types=[Term], actuals=[str])
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    def _decide_match(self, *, skip=None) -> None:  # pragma: no cover
        # if we're in line, line will check that our
        # contained Term, if any, matches.
        self.match = self.default_match()

    def resolve_value(self, skip=None) -> str | None:
        return None


class Wildcard(ValueProducer):
    """returns True to match, return value: the arg: 1-9+ or '*', or None.
    represents any number of headers"""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset(1)
        a.arg(types=[None, Term], actuals=[int, str])
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        if len(self.children) == 0:
            self.value = None
            return
        self.value = self.children[0].to_value(skip=skip)

    def _decide_match(self, *, skip=None) -> None:  # pragma: no cover
        # if we're in line, line will check that our
        # contained Term, if any, matches.
        self.match = self.default_match()

    def resolve_value(self, skip=None) -> str | None:
        return None
