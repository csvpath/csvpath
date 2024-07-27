from csvpath.matching.productions.expression import Matchable
from csvpath.matching.functions.function import Function
from csvpath.matching.functions.count import Count
from csvpath.matching.functions.regex import Regex
from csvpath.matching.functions.length import Length
from csvpath.matching.functions.notf import Not
from csvpath.matching.functions.now import Now
from csvpath.matching.functions.inf import In
from csvpath.matching.functions.concat import Concat
from csvpath.matching.functions.lower import Lower
from csvpath.matching.functions.upper import Upper
from csvpath.matching.functions.percent import Percent
from csvpath.matching.functions.below import Below
from csvpath.matching.functions.above import Above
from csvpath.matching.functions.first import First
from csvpath.matching.functions.count_lines import CountLines
from csvpath.matching.functions.count_scans import CountScans
from csvpath.matching.functions.orf import Or
from csvpath.matching.functions.no import No
from csvpath.matching.functions.yes import Yes
from csvpath.matching.functions.minf import Min, Max, Average
from csvpath.matching.functions.end import End
from csvpath.matching.functions.random import Random
from csvpath.matching.functions.add import Add
from csvpath.matching.functions.subtract import Subtract
from csvpath.matching.functions.multiply import Multiply
from csvpath.matching.functions.divide import Divide
from csvpath.matching.functions.tally import Tally
from csvpath.matching.functions.every import Every
from csvpath.matching.functions.printf import Print
from csvpath.matching.functions.increment import Increment
from csvpath.matching.functions.column import Column
from csvpath.matching.functions.substring import Substring
from csvpath.matching.functions.stop import Stop
from csvpath.matching.functions.any import Any
from csvpath.matching.functions.variable import Variable
from csvpath.matching.functions.header import Header
from csvpath.matching.functions.nonef import Nonef
from csvpath.matching.functions.last import Last
from csvpath.matching.functions.exists import Exists
from csvpath.matching.functions.mod import Mod
from csvpath.matching.functions.equals import Equals


class UnknownFunctionException(Exception):
    pass


class InvalidChildException(Exception):
    pass


class FunctionFactory:
    @classmethod
    def get_name_and_qualifier(self, name: str):
        aname = name
        qualifier = None
        dot = name.find(".")
        if dot > -1:
            aname = name[0:dot]
            qualifier = name[dot + 1 :]
            qualifier = qualifier.strip()
        return aname, qualifier

    @classmethod
    def get_function(  # noqa: C901
        cls, matcher, *, name: str, child: Matchable = None
    ) -> Function:
        if child and not isinstance(child, Matchable):
            raise InvalidChildException(f"{child} is not a valid child")
        f = None
        name, qualifier = cls.get_name_and_qualifier(name)
        if name == "count":
            f = Count(matcher, name, child)
        elif name == "length":
            f = Length(matcher, name, child)
        elif name == "regex":
            f = Regex(matcher, name, child)
        elif name == "not":
            f = Not(matcher, name, child)
        elif name == "now":
            f = Now(matcher, name, child)
        elif name == "in":
            f = In(matcher, name, child)
        elif name == "concat":
            f = Concat(matcher, name, child)
        elif name == "lower":
            f = Lower(matcher, name, child)
        elif name == "upper":
            f = Upper(matcher, name, child)
        elif name == "percent":
            f = Percent(matcher, name, child)
        elif name == "below":
            f = Below(matcher, name, child)
        elif name == "above":
            f = Above(matcher, name, child)
        elif name == "first":
            f = First(matcher, name, child)
        elif name == "count_lines":
            f = CountLines(matcher, name, child)
        elif name == "count_scans":
            f = CountScans(matcher, name, child)
        elif name == "or":
            f = Or(matcher, name, child)
        elif name == "no":
            f = No(matcher, name, child)
        elif name == "yes":
            f = Yes(matcher, name, child)
        elif name == "max":
            f = Max(matcher, name, child)
        elif name == "min":
            f = Min(matcher, name, child)
        elif name == "average":
            f = Average(matcher, name, child, "average")
        elif name == "median":
            f = Average(matcher, name, child, "median")
        elif name == "random":
            f = Random(matcher, name, child)
        elif name == "end":
            f = End(matcher, name, child)
        elif name == "length":
            f = Length(matcher, name, child)
        elif name == "add":
            f = Add(matcher, name, child)
        elif name == "subtract":
            f = Subtract(matcher, name, child)
        elif name == "multiply":
            f = Multiply(matcher, name, child)
        elif name == "divide":
            f = Divide(matcher, name, child)
        elif name == "tally":
            f = Tally(matcher, name, child)
        elif name == "every":
            f = Every(matcher, name, child)
        elif name == "print":
            f = Print(matcher, name, child)
        elif name == "increment":
            f = Increment(matcher, name, child)
        elif name == "column":
            f = Column(matcher, name, child)
        elif name == "substring":
            f = Substring(matcher, name, child)
        elif name == "stop":
            f = Stop(matcher, name, child)
        elif name == "variable":
            f = Variable(matcher, name, child)
        elif name == "header":
            f = Header(matcher, name, child)
        elif name == "any":
            f = Any(matcher, name, child)
        elif name == "none":
            f = Nonef(matcher, name, child)
        elif name == "last":
            f = Last(matcher, name, child)
        elif name == "exists":
            f = Exists(matcher, name, child)
        elif name == "mod":
            f = Mod(matcher, name, child)
        elif name == "equals":
            f = Equals(matcher, name, child)
        else:
            raise UnknownFunctionException(f"{name}")
        if child:
            child.parent = f
        if qualifier:
            f.set_qualifiers(qualifier)
        return f
