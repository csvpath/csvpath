# pylint: disable=C0114
import re
from csvpath.matching.util.expression_utility import ExpressionUtility
from ..function_focus import MatchDecider
from csvpath.matching.productions import Term, Variable, Header, Reference
from csvpath.matching.util.exceptions import ChildrenException
from ..function import Function
from ..args import Args


class Regex(MatchDecider):
    """does a regex match on a value"""

    def check_valid(self) -> None:
        self.args = Args(matchable=self)
        a = self.args.argset(3)
        a.arg(
            types=[Term, Variable, Header, Function, Reference],
            actuals=[str, self.args.EMPTY_STRING],
        )
        a.arg(
            types=[Term, Variable, Header, Function, Reference],
            actuals=[str, self.args.EMPTY_STRING],
        )
        a.arg(types=[None, Term, Variable, Header, Function, Reference], actuals=[int])
        self.args.validate(self.siblings())
        super().check_valid()
        left = self._function_or_equality.left
        self.is_regex_if(left)
        right = self._function_or_equality.right
        self.is_regex_if(right)

    def is_regex_if(self, t):
        if isinstance(t, Term):
            v = t.to_value()
            if v and len(v) > 0 and v[0] == "/":
                re.compile(v)

    def _the_regex(self, siblings, skip=None):
        # group
        group = 0 if len(siblings) == 2 else siblings[2].to_value(skip=skip)
        group = int(group)
        c1 = siblings[0]
        c2 = siblings[1]
        v1 = c1.to_value(skip=skip)
        v2 = c2.to_value(skip=skip)

        if v1.startswith("/"):
            theregex = v1.lstrip("/")
            theregex = theregex.rstrip("/")
            thevalue = v2
            return theregex, thevalue, group
        elif v2.startswith("/"):
            theregex = v2.lstrip("/")
            theregex = theregex.rstrip("/")
            thevalue = v1
            return theregex, thevalue, group
        else:
            # correct structure / children exception
            self.raiseChildrenException("No regular expression available")

    def _produce_value(self, skip=None) -> None:
        child = self.children[0]
        siblings = child.commas_to_list()
        theregex, thevalue, group = self._the_regex(siblings, skip=skip)
        if thevalue is None:
            # this could happen if the line is blank
            pass
        else:
            m = re.search(theregex, thevalue)
            # in the case of no match we're going to potentially
            # do extra regexing because self.value remains None
            # problem? self.match will be set so that may protect
            # us.
            v = None
            if m:
                v = m.group(group)
            if self.name == "regex":
                self.value = v
            elif self.name == "exact":
                self.value = v == thevalue
            s = f"Regex.to_value: mode: {self.name}, capture group at {group}: {v},"
            s = f"{s} with regex: {theregex}, original value: {thevalue},"
            s = f"{s} returning: {self.value}"
            self.matcher.csvpath.logger.info(s)

    def _decide_match(self, skip=None) -> None:
        if self.name == "regex":
            self.match = self.to_value(skip=skip) is not None
        elif self.name == "exact":
            self.match = ExpressionUtility.asbool(
                self.to_value(skip=skip)
            )  # pragma: no cover
