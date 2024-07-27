from csvpath.matching.productions.expression import Matchable
from .function import Function
from .count import Count
from .regex import Regex
from .length import Length
from .notf import Not
from .now import Now
from .inf import In
from .concat import Concat
from .lower import Lower
from .upper import Upper
from .percent import Percent
from .below import Below
from .above import Above
from .first import First
from .count_lines import CountLines
from .count_scans import CountScans
from .orf import Or
from .no import No
from .yes import Yes
from .minf import Min, Max, Average
from .end import End
from .random import Random
from .add import Add
from .subtract import Subtract
from .multiply import Multiply
from .divide import Divide
from .tally import Tally
from .every import Every
from .printf import Print
from .increment import Increment
from .column import Column
from .substring import Substring
from .stop import Stop
from .any import Any
from .variable import Variable
from .header import Header
from .nonef import Nonef
from .last import Last
from .exists import Exists
from .mod import Mod
from .equals import Equals


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
