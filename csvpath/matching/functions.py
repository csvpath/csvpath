from dataclasses import dataclass
from typing import Any
from csvpath.parser_utility import ParserUtility
from csvpath.matching.expression import Function, Term
import re

class Count(Function):

    # [@b = count(#name = 'fish')]
    def to_value(self) -> Any:
        if self.function_or_equality:
            return self.get_contained_value()
        else:
            if not self.matcher.csvpath:
                print("WARNING: no csvpath. are we testing?")
                return
            self.matcher.csvpath.match_count + 1 # we're eager to +1 because we don't
                                                 # contribute to if there's a match
                                                 # or not. we have to act as if.

    def get_contained_value():
        #
        # need to apply this count function to the contained obj's value
        #
        b = self.function_or_equality.matches()
        myid = self.get_id(self.function_or_equality)
        tracked_value = self.function_or_equality.to_value()
        cnt = self.matcher.get_variable(myid, tracking=tracked_value)
        cnt = cnt + 1
        self.matcher.set_variable(myid, tracking=tracked_value, count=cnt)
        return val

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





