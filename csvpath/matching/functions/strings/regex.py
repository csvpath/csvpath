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
        d = None
        if self.name == "exact":
            d = self.wrap(
                """\
                Looks for an exact match, with unmatched preceding or trailing characters,
                of a regular expression to a string.

                The regular expression can be in argument one or two.
            """
            )
        else:
            d = self.wrap(
                """\
                Matches a regular expression to a string.

                The regular expression can be in argument one or two.

                Optionally, the third argument returns a group from the
                match, if any groups were defined.
            """
            )

        self.description = [self._cap_name(), d]
        self.match_qualifiers.append("asbool")
        self.args = Args(matchable=self)
        a = self.args.argset(3)
        a.arg(
            name="str or regex",
            types=[Term, Variable, Header, Function, Reference],
            actuals=[str, self.args.EMPTY_STRING, None],
        )
        #
        # because we accept the regex in 0 or 1 we have to accept None
        # as an actual value in both.
        #
        a.arg(
            name="str or regex",
            types=[Term, Variable, Header, Function, Reference],
            actuals=[str, self.args.EMPTY_STRING, None],
        )
        a.arg(
            name="group",
            types=[None, Term, Variable, Header, Function, Reference],
            actuals=[int],
        )
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
            msg = "No regular expression available"
            self.matcher.csvpath.error_manager.handle_error(source=self, msg=msg)
            if self.matcher.csvpath.do_i_raise():
                raise ChildrenException(msg)

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
            s = "Regex.to_value: mode: %s, capture group at %s: %s, with regex: %s, original value: %s, returning: %s"
            self.matcher.csvpath.logger.debug(
                s, self.name, group, v, theregex, thevalue, self.value
            )

    def _decide_match(self, skip=None) -> None:
        if self.name == "regex":
            self.match = self.to_value(skip=skip) is not None
        elif self.name == "exact":
            self.match = ExpressionUtility.asbool(
                self.to_value(skip=skip)
            )  # pragma: no cover
