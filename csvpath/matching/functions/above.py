from typing import Any
from csvpath.matching.functions.function import Function, ChildrenException
import datetime

class Above(Function):

    def to_value(self) -> Any:
        if len(self.children) != 1:
            self.matcher.print(f"Above.to_value: must have 1 equality child: {self.children}")
            raise ChildrenException("Above function must have 1 child")
        if self.children[0].op != ",":
            raise ChildrenException(f"Above function must have an equality with the ',' operation, not {self.children[0].op}")
        thischild = self.children[0].children[0]
        abovethatchild = self.children[0].children[1]

        this_is = thischild.to_value()
        above_that = abovethatchild.to_value()
        this = -1
        that = -1
        try:
            this = float(this_is)
            that = float(above_that)
        except:
            raise Exception(f"Above.to_value: this: {this}, a {this.__class__}, and {that}, a {that.__class__}")
        b = this > that
        return b

    def matches(self) -> bool:
        return self.to_value()




