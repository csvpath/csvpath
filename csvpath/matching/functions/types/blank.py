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


class Blank(Type):
    """returns True to match, returns its child's value or None. represents any value"""

    def check_valid(self) -> None:
        self.aliases = ["blank", "nonspecific", "unspecified"]
        self.match_qualifiers.append("distinct")
        self.description = [
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
        #
        # Note: this was default_match() but that method returns self.matcher._AND. when OR
        # blank() would return False, when we actually want it to be True here. matcher will
        # take care of the OR flip itself. leaving this note in case it comes up again here
        # or elsewhere.
        #
        # to be clear: matchable.default_match() is correct. But it is not applicable for a
        # type within line(). blank() is only used in line().
        #
        self.match = True
