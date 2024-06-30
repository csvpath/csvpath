from typing import Any
from csvpath.matching.productions.term import Term
from csvpath.matching.functions.function import Function
import re


class Regex(Function):

    def to_value(self) -> Any:
        self.matches()

    def matches(self) -> bool:
        left = self._function_or_equality.left
        right = self._function_or_equality.right

        self.matcher.print(f"Regex.matches: equality.left: {left} .right: {right}")

        regex = None
        value = None
        if isinstance(left, Term):
            regex = left
            value = right
        else:
            regex = right
            value = left

        thevalue = value.to_value()
        theregex = regex.to_value()
        if theregex[0] == '/':
            theregex = theregex[1:]
        if theregex[len(theregex)-1] == '/':
            theregex = theregex[0:len(theregex)-1]

        self.matcher.print(f"regex.matches: thevalue: {thevalue}, the regex: {theregex}")
        return re.fullmatch(theregex, thevalue)





