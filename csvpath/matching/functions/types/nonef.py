# pylint: disable=C0114
from typing import Any
from csvpath.matching.util.expression_utility import ExpressionUtility
from csvpath.matching.util.exceptions import ChildrenException, MatchException
from csvpath.matching.productions import Variable, Header, Reference, Term, Equality
from csvpath.matching.functions.function import Function
from ..args import Args
from ..function import CheckedUnset
from ..function_focus import ValueProducer
from .type import Type


class Nonef(ValueProducer, Type):
    """returns None"""

    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
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
    def _is_match(
        cls,
        value: str,
    ) -> tuple[bool, str | None]:
        return ExpressionUtility.is_none(value)


class Blank(Type):
    """returns True to match, returns its child's value or None. represents any value"""

    def check_valid(self) -> None:
        self.aliases = ["blank", "nonspecific", "unspecified"]
        self.match_qualifiers.append("distinct")
        self.description = [
            self._cap_name(),
            "A line() schema type representing an incompletely known header.",
            "Blank cannot be used outside a line()",
        ]
        #
        # WE DON'T WANT blank() USED IN PLACE OF none(), empty() OR AN EXISTANCE TEST
        # WHEN NOT USED IN LINE:
        #    x = blank() ERROR
        #    blank(#0) ERROR
        #    blank() -> @x = "y" ERROR
        #    blank(#0) -> @x = "y" ERROR
        #
        # and actually blank() in line() now errors no matter what.
        #
        if (
            self.parent is None
            or not isinstance(self.parent, Equality)
            or not self.parent.parent
            or not str(type(self.parent.parent)).find(".Line'") > -1
        ):
            raise ChildrenException("Blank can only be used within a line schema")
        #
        #
        #
        self.args = Args(matchable=self)
        #
        #
        #
        self.args.argset(0)
        #
        #
        #
        a = self.args.argset(1)
        a.arg(types=[Header], actuals=[str, None, self.args.EMPTY_STRING, Any])
        #
        #
        #
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        #
        # this doesn't match comment above. according to comment we return the
        # value of the header represented. calling match does nothing.
        #
        self.value = self.matches(skip=skip)
        #
        #
        #

    def _decide_match(self, skip=None) -> None:  # pragma: no cover
        # if we're in line, line will check that our
        # contained Term, if any, matches.
        if self.distinct:
            if len(self.siblings()) > 0:
                self._distinct_if(skip=skip)
            else:
                sibs = self.parent.siblings()
                i = sibs.index(self)
                if i > -1 and len(self.matcher.line) > i:
                    value = self.matcher.line[i]
                    self._distinct_if(skip=skip, value=value)
                else:
                    self.value = CheckedUnset()
                    msg = "Header {i} not found"
                    self.matcher.csvpath.error_manager.handle_error(
                        source=self, msg=msg
                    )
                    if self.matcher.csvpath.do_i_raise():
                        raise MatchException(msg)
        if self.notnone:
            v = None
            if len(self.siblings()) > 0:
                v = self._value_one(skip=skip)
            else:
                sibs = self.parent.siblings()
                i = sibs.index(self)
                if i > -1 and len(self.matcher.line) > i:
                    v = self.matcher.line[i]
            if v is None or str(v).strip() == "":
                self.value = CheckedUnset()
                msg = "Header {i} cannot be empty because notnone is set"
                self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
                if self.matcher.csvpath.do_i_raise():
                    raise MatchException(msg)
        self.match = self.default_match()


class Wildcard(Type):
    """returns True to match, return value: the arg: 1-9+ or '*', or None.
    represents any number of headers"""

    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            f"A {self.name}() schema type represents one or more headers that are otherwise unspecified.",
            "It may take an int indicating the number of headers or a * to indicate any number of headers.",
            """When wildcard() has no args it represents any nuber of headers, same as "*".""",
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
