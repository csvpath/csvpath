# pylint: disable=C0114
from typing import Any
from ..function_focus import MatchDecider
from csvpath.matching.productions import Header, Variable, Equality, Term
from csvpath.matching.util.exceptions import ChildrenException
from ..headers.headers import Headers
from csvpath.matching.util.expression_utility import ExpressionUtility
from csvpath.matching.functions.args import Args
from csvpath.matching.functions.function import Function


class Empty(MatchDecider):
    """checks for empty or blank header values in a given line.
    it reports True only if all the places it is directed to look are empty.
    if you pass it headers() it checks for all headers being empty."""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        #
        # we'd like to disallow headers from taking a value in this case, but we
        # cannot because headers is a function and will be covered by the second
        # argset, so we handle that in a helper validation function.
        #
        a = self.args.argset(1)
        a.arg(types=[Headers])
        a = self.args.argset()
        a.arg(types=[Variable, Function, Header], actuals=[None, Any])
        self.args.validate(self.siblings())
        #
        self._validate()
        super().check_valid()  # pragma: no cover

    def _validate(self):
        sibs = self.siblings()
        for s in sibs:
            # both structure / children exceptions
            if isinstance(s, Headers) and len(sibs) > 1:
                self.raiseChildrenException(
                    "If empty() has a headers() argument it can only have 1 argument"
                )
            if isinstance(s, Term):
                self.raiseChildrenException(
                    "empty() arguments cannot include terms"
                )  # pragma: no cover

    def _produce_value(self, skip=None) -> None:
        self.value = self.matches(skip=skip)

    #
    # empty(headers())
    # empty(#h, #h2, hn...)
    # empty(var=list)
    # empty(var=dict)
    # empty(var)
    # empty(ref)
    #
    def _decide_match(self, skip=None) -> None:
        if len(self.children) == 1 and isinstance(self.children[0], Headers):
            self._do_headers(skip=skip)
        elif len(self.children) == 1 and isinstance(self.children[0], Equality):
            self._do_many(skip=skip)
        elif len(self.children) == 1:
            self._do_one(self.children[0], skip=skip)
        else:
            self._do_many(skip=skip)

    def _do_headers(self, skip=None):
        ret = True
        for i, h in enumerate(self.matcher.line):
            ret = ExpressionUtility.is_empty(h)
            if ret is False:
                break
        self.match = ret

    def _do_many(self, skip=None):
        siblings = self.siblings()
        for s in siblings:
            self._do_one(s)
            if self.match is False:
                break

    def _do_one(self, child, skip=None):
        v = child.to_value(skip=skip)
        self.match = ExpressionUtility.is_empty(v)
