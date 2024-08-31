from csvpath.matching.productions.expression import Matchable
from .function import Function
from .count import Count
from .regex import Regex
from .length import Length, MinMaxLength
from .notf import Not
from .now import Now
from .inf import In
from .concat import Concat
from .lower import Lower
from .upper import Upper
from .percent import Percent
from .above import AboveBelow
from .between import Between
from .first import First
from .count_lines import CountLines, LineNumber
from .count_scans import CountScans
from .count_headers import CountHeaders
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
from .round import Round

#
# Column is deprecated, HeaderName has same
# function and more, and matches the terminology
#
from .column import Column, HeaderName, HeaderNamesMismatch
from .substring import Substring
from .starts_with import StartsWith
from .stop import Stop, Skip
from .any import Any
from .variable import Variable
from .header import Header
from .nonef import Nonef
from .last import Last
from .exists import Exists
from .mod import Mod
from .equals import Equals
from .strip import Strip
from .jinjaf import Jinjaf
from .correlate import Correlate
from .percent_unique import PercentUnique
from .all import All
from .total_lines import TotalLines
from .pushpop import Push, PushDistinct, Pop, Peek, PeekSize, Stack
from .datef import Date
from .fail import Fail
from .failed import Failed
from .stdev import Stdev
from .dups import HasDups
from .empty import Empty
from .first_line import FirstLine
from .advance import Advance
from .collect import Collect
from .intf import Int
from .andf import And
from .track import Track
from .sum import Sum
from .reset_headers import ResetHeaders
from .mismatch import Mismatch
from .after_blank import AfterBlank
from .importf import Import


class UnknownFunctionException(Exception):
    pass


class InvalidNameException(Exception):
    pass


class InvalidChildException(Exception):
    pass


class FunctionFactory:

    NOT_MY_FUNCTION = {}

    @classmethod
    def add_function(cls, name: str, function: Function) -> None:
        if name is None:
            name = function.name
        if name is None:
            raise InvalidNameException("Name passed in with function cannot be None")
        if not isinstance(name, str):
            raise InvalidNameException("Name must be a string")
        name = name.strip()
        if name == "":
            raise InvalidNameException("Name must not be an empty string")
        if not name.isalpha():
            raise InvalidNameException("Name must alpha characters only")
        if cls.get_function(None, name=name, find_external_functions=False) is not None:
            raise InvalidNameException("Built-in functions cannot be overriden")
        if not isinstance(function, Function):
            #
            # pass as an instance, not a class, for specificity. good to do?
            #
            raise InvalidChildException(
                "Function being registered must be passed as an instance"
            )
        cls.NOT_MY_FUNCTION[name] = function.__class__

    @classmethod
    def get_name_and_qualifier(cls, name: str):
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
        cls,
        matcher,
        *,
        name: str,
        child: Matchable = None,
        find_external_functions: bool = True,
    ) -> Function:
        #
        # matcher must be Noneable for add_function
        #
        if child and not isinstance(child, Matchable):
            raise InvalidChildException(f"{child} is not a valid child")
        f = None
        name, qualifier = cls.get_name_and_qualifier(name)
        if name == "count":
            f = Count(matcher, name, child)
        elif name == "length":
            f = Length(matcher, name, child)
        elif name == "regex" or name == "exact":
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
        elif name == "below" or name == "lt" or name == "before":
            f = AboveBelow(matcher, name, child)
        elif name == "above" or name == "gt" or name == "after":
            f = AboveBelow(matcher, name, child)
        elif name == "first":
            f = First(matcher, name, child)
        elif name == "firstline" or name == "firstmatch" or name == "firstscan":
            f = FirstLine(matcher, name, child)
        elif name == "count_lines":
            f = CountLines(matcher, name, child)
        elif name == "count_scans":
            f = CountScans(matcher, name, child)
        elif name == "or":
            f = Or(matcher, name, child)
        elif name == "no" or name == "false":
            f = No(matcher, name, child)
        elif name == "yes" or name == "true":
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
        elif name == "subtract" or name == "minus":
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
        elif (
            name == "header_name"
            or name == "header_index"
            or name == "header_name_mismatch"
        ):
            f = HeaderName(matcher, name, child)
        elif name == "header_names_mismatch":
            f = HeaderNamesMismatch(matcher, name, child)
        elif name == "substring":
            f = Substring(matcher, name, child)
        elif name == "stop" or name == "fail_and_stop":
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
        elif name == "strip":
            f = Strip(matcher, name, child)
        elif name == "jinja":
            f = Jinjaf(matcher, name, child)
        elif name == "correlate":
            f = Correlate(matcher, name, child)
        elif name == "count_headers" or name == "count_headers_in_line":
            f = CountHeaders(matcher, name, child)
        elif name == "percent_unique":
            f = PercentUnique(matcher, name, child)
        elif name == "all":
            f = All(matcher, name, child)
        elif name == "total_lines":
            f = TotalLines(matcher, name, child)
        elif name == "push":
            f = Push(matcher, name, child)
        elif name == "push_distinct":
            f = PushDistinct(matcher, name, child)
        elif name == "pop":
            f = Pop(matcher, name, child)
        elif name == "peek":
            f = Peek(matcher, name, child)
        elif name == "peek_size" or name == "size":
            f = PeekSize(matcher, name, child)
        elif name == "date" or name == "datetime":
            f = Date(matcher, name, child)
        elif name == "fail":
            f = Fail(matcher, name, child)
        elif name == "failed" or name == "valid":
            f = Failed(matcher, name, child)
        elif name == "stack":
            f = Stack(matcher, name, child)
        elif name == "stdev" or name == "pstdev":
            f = Stdev(matcher, name, child)
        elif name == "has_dups":
            f = HasDups(matcher, name, child)
        elif name == "empty":
            f = Empty(matcher, name, child)
        elif name == "advance":
            f = Advance(matcher, name, child)
        elif name == "collect":
            f = Collect(matcher, name, child)
        elif name == "int":
            f = Int(matcher, name, child)
        elif name == "and":
            f = And(matcher, name, child)
        elif name == "track":
            f = Track(matcher, name, child)
        elif name == "sum":
            f = Sum(matcher, name, child)
        elif name == "reset_headers":
            f = ResetHeaders(matcher, name, child)
        elif name == "starts_with":
            f = StartsWith(matcher, name, child)
        elif name == "skip":
            f = Skip(matcher, name, child)
        elif name == "mismatch":
            f = Mismatch(matcher, name, child)
        elif name == "line_number":
            f = LineNumber(matcher, name, child)
        elif name == "after_blank":
            f = AfterBlank(matcher, name, child)
        elif name == "round":
            f = Round(matcher, name, child)
        elif name == "import":
            f = Import(matcher, name, child)
        elif (
            name == "min_length"
            or name == "max_length"
            or name == "too_long"
            or name == "too_short"
        ):
            f = MinMaxLength(matcher, name, child)
        elif (
            name == "between"
            or name == "inside"
            or name == "beyond"
            or name == "outside"
        ):
            f = Between(matcher, name, child)
        else:
            if (
                f is None
                and find_external_functions
                and name in FunctionFactory.NOT_MY_FUNCTION
            ):
                f = cls.NOT_MY_FUNCTION[name]
                f = f(matcher, name, child)
            if not find_external_functions:
                return None
            if f is None:
                raise UnknownFunctionException(f"{name}")
        if child:
            child.parent = f
        if qualifier:
            f.set_qualifiers(qualifier)
        if f.matcher is None:
            f.matcher = matcher
        return f
