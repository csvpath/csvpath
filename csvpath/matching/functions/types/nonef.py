# pylint: disable=C0114
from typing import Any
from csvpath.matching.util.expression_utility import ExpressionUtility
from csvpath.matching.util.exceptions import ChildrenException, MatchException
from csvpath.matching.productions import Variable, Header, Reference, Term
from csvpath.matching.functions.function import Function
from ..args import Args
from ..function_focus import ValueProducer
from .type import Type


class Nonef(ValueProducer, Type):
    def check_valid(self) -> None:
        self.description = [
            "A value producer and line() schema type representing a None value.",
        ]
        self.args = Args(matchable=self)
        self.args.argset(0)
        a = self.args.argset(1)
        a.arg(
            name="nullable",
            types=[Variable, Header, Function, Reference],
            actuals=[None],
        )
        a = self.args.argset(1)
        a.arg(name="header reference", types=[Term], actuals=[str])
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.value = None

    def _decide_match(self, skip=None) -> None:  # pragma: no cover
        if len(self.children) == 0:
            self.match = True
        if isinstance(self._child_one(), Term):
            v = self._value_one(skip=skip)
            h = self.matcher.get_header_value(v)
            self.match = ExpressionUtility.is_none(h)
            if self.match is False:
                msg = f"'{v}' must be empty"
                self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
                if self.matcher.csvpath.do_i_raise():
                    raise MatchException(msg)
        else:
            self.match = ExpressionUtility.is_none(self._value_one(skip=skip))

    @classmethod
    def _is_match(cls, value: str, *, strict: bool = False) -> tuple[bool, str | None]:
        if strict is True and value is not None:
            return False
        return ExpressionUtility.is_none(value)


class Wildcard(Type):
    def check_valid(self) -> None:
        self.description = [
            f"A {self.name}() schema type represents one or more headers that are otherwise unspecified.",
            "It may take an int indicating the number of headers or a * to indicate any number of headers.",
            """When wildcard() has no args it represents any number of headers, same as "*".""",
            """Note that wildcard() can represent 0 headers. Essentially, a wildcard by itself will not
            invalidate a document unless it defines a specific number of headers that are not found.""",
        ]
        self.args = Args(matchable=self)
        #
        # 0-len argset
        #
        a = self.args.argset()
        #
        # 1-len argset
        #
        a = self.args.argset(1)
        a.arg(types=[Term], actuals=[int, str, None, Any])
        self.args.validate(self.siblings())
        #
        # should check for int or * here.
        # should we be even more perscriptive and check that this is a:
        #    line->equality->wildcard
        # path? as-is, it allows deeper nesting which we don't want.
        #
        if ExpressionUtility.get_ancestor(self, "Line") is None:
            msg = "Wildcard can only be used within line()"
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
            if self.matcher.csvpath.do_i_raise():
                raise ChildrenException(msg)
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        if len(self.children) == 0:
            self.value = None
            return
        #
        # do we really want to be returning a value from a wildcard that may represent
        # any number of headers?
        #
        self.value = self.children[0].to_value(skip=skip)

    def _decide_match(self, skip=None) -> None:  # pragma: no cover
        # if we're in line, line will check that our
        # contained Term, if any, matches.
        self.match = self.default_match()
