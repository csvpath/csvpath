from typing import Any
from ..productions import Term
from .function import Function
import re


class Regex(Function):
    def to_value(self, *, skip=[]) -> Any:
        self.matches(skip=skip)

    def matches(self, *, skip=[]) -> bool:
        if self in skip:
            return True
        if self.match is None:
            left = self._function_or_equality.left
            right = self._function_or_equality.right
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

            self.match = re.search(theregex, thevalue) is not None
            # print(f"Regex.matches: theregex: {theregex}, thevalue: {thevalue}, self.match: {self.match}")
        return self.match
