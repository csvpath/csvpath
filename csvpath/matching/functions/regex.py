from typing import Any
from ..productions import Term
from .function import Function
import re


class Regex(Function):
    def check_valid(self) -> None:
        self.validate_two_or_three_args()
        super().check_valid()
        left = self._function_or_equality.left
        right = self._function_or_equality.right
        if isinstance(left, Term):
            restr = left.to_value()
        else:
            restr = right.to_value()
        re.compile(restr)

    def to_value(self, *, skip=[]) -> Any:
        if self in skip:  # pragma: no cover
            return self._noop_value()
        if self.value is None:
            child = self.children[0]
            siblings = child.commas_to_list()
            if len(siblings) < 2 or len(siblings) > 3:
                raise Exception(
                    "wrong number of siblings. should have been caught in check_valid!"
                )
            left = siblings[0]
            right = siblings[1]
            group = 0 if len(siblings) == 2 else siblings[2].to_value()
            group = int(group)
            regex = None
            value = None
            if isinstance(left, Term):
                regex = left
                value = right
            else:
                regex = right
                value = left
            thevalue = value.to_value(skip=skip)
            theregex = regex.to_value(skip=skip)
            if theregex[0] == "/":
                theregex = theregex[1:]
            if theregex[len(theregex) - 1] == "/":
                theregex = theregex[0 : len(theregex) - 1]
            m = re.search(theregex, thevalue)
            # in the case of no match we're going to potentially
            # do extra regexing because self.value remains None
            # problem? self.match will be set so that may protect
            # us.
            self.value = m.group(group) if m is not None else None
        return self.value

    def matches(self, *, skip=[]) -> bool:
        if self in skip:  # pragma: no cover
            return self._noop_match()
        print(f"Regex.matches: self.match: {self.match}")
        if self.match is None:
            self.match = self.to_value(skip=skip) is not None
        return self.match
