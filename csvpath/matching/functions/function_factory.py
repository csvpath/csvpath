# pylint: disable=C0114
from csvpath.matching.productions.expression import Matchable
from .function import Function
from .strings.lower import Lower
from .strings.upper import Upper
from .strings.substring import Substring
from .strings.starts_with import StartsWith
from .strings.strip import Strip
from .strings.length import Length, MinMaxLength
from .strings.concat import Concat
from .strings.metaphone import Metaphone
from .counting.count import Count
from .counting.count_lines import CountLines, LineNumber
from .counting.count_scans import CountScans
from .counting.count_headers import CountHeaders
from .counting.total_lines import TotalLines
from .counting.tally import Tally
from .counting.every import Every
from .counting.increment import Increment
from .headers.reset_headers import ResetHeaders
from .headers.header_name import HeaderName
from .headers.header_names_mismatch import HeaderNamesMismatch
from .headers.headers import Headers
from .headers.mismatch import Mismatch
from .headers.end import End
from .math.above import AboveBelow
from .math.add import Add
from .math.subtract import Subtract
from .math.multiply import Multiply
from .math.divide import Divide
from .math.sum import Sum
from .math.equals import Equals
from .math.round import Round
from .math.mod import Mod
from .boolean.notf import Not
from .boolean.inf import In
from .boolean.orf import Or
from .boolean.empty import Empty
from .boolean.no import No
from .boolean.yes import Yes
from .boolean.between import Between
from .boolean.andf import And
from .boolean.any import Any
from .boolean.all import All
from .boolean.exists import Exists
from .stats.percent import Percent
from .stats.minf import Min, Max, Average
from .stats.percent_unique import PercentUnique
from .stats.stdev import Stdev
from .stats.correlate import Correlate
from .print.printf import Print
from .print.print_line import PrintLine
from .print.jinjaf import Jinjaf
from .print.print_queue import PrintQueue
from .lines.stop import Stop, Skip
from .lines.first import First
from .lines.last import Last
from .lines.dups import HasDups, DupLines, CountDups
from .lines.first_line import FirstLine
from .lines.advance import Advance
from .lines.after_blank import AfterBlank
from .misc.random import Random
from .misc.regex import Regex
from .misc.now import Now
from .misc.variables import Variables
from .misc.nonef import Nonef
from .misc.pushpop import Push, PushDistinct, Pop, Peek, PeekSize, Stack
from .misc.datef import Date
from .misc.collect import Collect
from .misc.replace import Replace
from .misc.intf import Int
from .misc.get import Get
from .misc.track import Track
from .misc.importf import Import
from .misc.debug import Debug, BriefStackTrace, VoteStack
from .validity.failed import Failed
from .validity.fail import Fail


class UnknownFunctionException(Exception):
    """thrown when the name used is not registered"""


class InvalidNameException(Exception):
    """thrown when a name is for some reason not allowed"""


class InvalidChildException(Exception):
    """thrown when an incorrect subclass is seen;
    e.g. a function that is not Function."""


class FunctionFactory:
    """this class creates instances of functions according to what
    name is used in a csvpath"""

    NOT_MY_FUNCTION = {}

    @classmethod
    def add_function(cls, name: str, function: Function) -> None:
        """use to add a new, external function at runtime"""
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
            # pass as an instance, not a class, for specificity. good to do?
            raise InvalidChildException(
                "Function being registered must be passed as an instance"
            )
        cls.NOT_MY_FUNCTION[name] = function.__class__

    @classmethod
    def get_name_and_qualifier(cls, name: str):  # pylint: disable=C0116
        aname = name
        qualifier = None
        dot = name.find(".")
        if dot > -1:
            aname = name[0:dot]
            qualifier = name[dot + 1 :]
            qualifier = qualifier.strip()
        return aname, qualifier

    @classmethod
    def get_function(  # noqa: C901 #pylint: disable=C0116,R0912, R0915
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
        qname = name
        name, qualifier = cls.get_name_and_qualifier(name)
        if name == "count":
            f = Count(matcher, name, child)
        elif name == "length":
            f = Length(matcher, name, child)
        elif name in ["regex", "exact"]:
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
        elif name in ["below", "lt", "before"]:
            f = AboveBelow(matcher, name, child)
        elif name in ["above", "gt", "after"]:
            f = AboveBelow(matcher, name, child)
        elif name == "first":
            f = First(matcher, name, child)
        elif name in ["firstline", "firstmatch", "firstscan"]:
            f = FirstLine(matcher, name, child)
        elif name == "count_lines":
            f = CountLines(matcher, name, child)
        elif name == "count_scans":
            f = CountScans(matcher, name, child)
        elif name == "or":
            f = Or(matcher, name, child)
        elif name in ["no", "false"]:
            f = No(matcher, name, child)
        elif name in ["yes", "true"]:
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
        elif name in ["subtract", "minus"]:
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
        elif name in ["header_name", "header_index"]:
            f = HeaderName(matcher, name, child)
        elif name == "header_names_mismatch":
            f = HeaderNamesMismatch(matcher, name, child)
        elif name == "substring":
            f = Substring(matcher, name, child)
        elif name in ["stop", "fail_and_stop"]:
            f = Stop(matcher, name, child)
        elif name == "variables":
            f = Variables(matcher, name, child)
        elif name == "headers":
            f = Headers(matcher, name, child)
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
        elif name in ["equals", "eq"]:
            f = Equals(matcher, name, child)
        elif name == "strip":
            f = Strip(matcher, name, child)
        elif name == "jinja":
            f = Jinjaf(matcher, name, child)
        elif name == "correlate":
            f = Correlate(matcher, name, child)
        elif name in ["count_headers", "count_headers_in_line"]:
            f = CountHeaders(matcher, name, child)
        elif name == "percent_unique":
            f = PercentUnique(matcher, name, child)
        elif name in ["missing", "all"]:
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
        elif name in ["peek_size", "size"]:
            f = PeekSize(matcher, name, child)
        elif name in ["date", "datetime"]:
            f = Date(matcher, name, child)
        elif name == "fail":
            f = Fail(matcher, name, child)
        elif name in ["failed", "valid"]:
            f = Failed(matcher, name, child)
        elif name == "stack":
            f = Stack(matcher, name, child)
        elif name in ["stdev", "pstdev"]:
            f = Stdev(matcher, name, child)
        #
        # dup_lines can also decide matches
        #
        elif name == "has_dups":
            f = HasDups(matcher, name, child)
        elif name == "count_dups":
            f = CountDups(matcher, name, child)
        elif name == "dup_lines":
            f = DupLines(matcher, name, child)
        elif name == "empty":
            f = Empty(matcher, name, child)
        elif name == "advance":
            f = Advance(matcher, name, child)
        elif name == "collect":
            f = Collect(matcher, name, child)
        elif name == "replace":
            f = Replace(matcher, name, child)
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
        elif name == "print_line":
            f = PrintLine(matcher, name, child)
        elif name == "print_queue":
            f = PrintQueue(matcher, name, child)
        elif name in ["min_length", "max_length", "too_long", "too_short"]:
            f = MinMaxLength(matcher, name, child)
        elif name in ["between", "inside", "beyond", "outside", "from_to"]:
            f = Between(matcher, name, child)
        elif name == "get":
            f = Get(matcher, name, child)
        elif name == "debug":
            f = Debug(matcher, name, child)
        elif name == "brief_stack_trace":
            f = BriefStackTrace(matcher, name, child)
        elif name == "vote_stack":
            f = VoteStack(matcher, name, child)
        elif name == "metaphone":
            f = Metaphone(matcher, name, child)
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
            f.qualified_name = qname
        if f.matcher is None:
            f.matcher = matcher
        return f
