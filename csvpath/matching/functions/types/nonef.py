# pylint: disable=C0114
from csvpath.matching.util.expression_utility import ExpressionUtility
from csvpath.matching.util.exceptions import ChildrenException, MatchException
from csvpath.matching.productions import Variable, Header, Reference, Term
from csvpath.matching.functions.function import Function
from ..args import Args
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
            h = self.matcher.get_header_value(self, v)
            self.match = ExpressionUtility.is_none(h)
            if self.match is False:
                msg = f"'{v}' must be empty"
                self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
                if self.matcher.csvpath.do_i_raise():
                    raise MatchException(msg)
        else:
            self.match = ExpressionUtility.is_none(self._value_one(skip=skip))


class Blank(ValueProducer, Type):
    """returns True to match, returns its child's value or None. represents any value"""

    def check_valid(self) -> None:
        self.aliases = ["blank", "nonspecific", "unspecified"]
        self.description = [
            self._cap_name(),
            "A line() schema type representing an incompletely specified header.",
            "It can take a string naming its positional header.",
        ]
        self.args = Args(matchable=self)
        self.args.argset(0)
        a = self.args.argset(1)
        a.arg(types=[Header], actuals=[str, None, self.args.EMPTY_STRING])
        self.args.validate(self.siblings())
        super().check_valid()

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    def _decide_match(self, skip=None) -> None:  # pragma: no cover
        # if we're in line, line will check that our
        # contained Term, if any, matches.
        self.match = self.default_match()


class Wildcard(ValueProducer, Type):
    """returns True to match, return value: the arg: 1-9+ or '*', or None.
    represents any number of headers"""

    def check_valid(self) -> None:
        self.description = [
            self._cap_name(),
            f"A {self.name}() schema type represents one or more headers that are otherwise unspecified.",
            "It may take an int indicating the number of headers or a * to indicate any number of headers.",
        ]
        self.args = Args(matchable=self)
        a = self.args.argset(1)
        a.arg(types=[None, Term], actuals=[int, str])
        self.args.validate(self.siblings())
        #
        # should check for int or * here
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
        self.value = self.children[0].to_value(skip=skip)

    def _decide_match(self, skip=None) -> None:  # pragma: no cover
        # if we're in line, line will check that our
        # contained Term, if any, matches.
        self.match = self.default_match()
