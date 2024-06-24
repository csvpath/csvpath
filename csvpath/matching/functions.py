from dataclasses import dataclass
from typing import Any
from csvpath.parser_utility import ParserUtility
from csvpath.matching.expression import Function, Term
import re

class Count(Function):

    def to_value(self) -> Any:
        if self.function_or_equality:
            #
            # need to apply this count function to the contained obj's value
            #
            b = self.function_or_equality.matches()
            val = self.matcher.csvpath.get_variable(self.get_id())
            val = val+1
            self.matcher.csvpath.set_variable(self.get_id(), val)
            return val
        # add 1 so that if we are a match we match on the
        # right number of matches, and if we don't we'll check the same way next time
        mc = 0
        if not self.matcher.csvpath:
            print("WARNING: csvpath is None. are we unit testing?!")
            mc = 1
        else:
            mc = self.matcher.csvpath.match_count + 1
        return mc

class Regex(Function):

    def to_value(self) -> Any:
        self.matches()

    def matches(self) -> bool:
        left = self.function_or_equality.left
        right = self.function_or_equality.right

        print(f"Regex.matches: equality.left: {left} .right: {right}")

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

        print(f"regex.matches: thevalue: {thevalue}, the regex: {theregex}")
        return re.fullmatch(theregex, thevalue)





