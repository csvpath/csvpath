# pylint: disable=C0114
from csvpath.matching.productions.expression import Matchable
from .function import Function
from .function_finder import FunctionFinder
from .dates.now import Now
from .strings.lower import Lower
from .strings.contains import Contains
from .strings.upper import Upper
from .strings.caps import Capitalize
from .strings.substring import Substring
from .strings.starts_with import StartsWith
from .strings.strip import Strip
from .strings.length import Length, MinMaxLength
from .strings.regex import Regex
from .strings.concat import Concat
from .strings.alter import Alter
from .strings.metaphone import Metaphone
from .counting.count import Count
from .counting.count_bytes import CountBytes
from .counting.counter import Counter
from .counting.has_matches import HasMatches
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
from .headers.collect import Collect
from .headers.replace import Replace
from .headers.append import Append
from .headers.insert import Insert
from .headers.headers import Headers
from .headers.empty_stack import EmptyStack
from .headers.mismatch import Mismatch
from .headers.end import End
from .math.above import AboveBelow
from .math.add import Add
from .math.subtract import Subtract
from .math.multiply import Multiply
from .math.divide import Divide
from .math.intf import Int, Float  # , Num
from .math.odd import Odd
from .math.sum import Sum
from .math.subtotal import Subtotal
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

# from .stats.minf import Min, Max, Average, Median
from .stats.minf import Average, Median
from .stats.nminmax import Min, Max
from .stats.percent_unique import PercentUnique
from .stats.stdev import Stdev
from .print.printf import Print
from .print.table import HeaderTable, RowTable, VarTable, RunTable
from .print.print_line import PrintLine
from .print.jinjaf import Jinjaf
from .print.print_queue import PrintQueue
from .lines.stop import Stop, Skip, StopAll, SkipAll
from .lines.first import First
from .lines.last import Last
from .lines.dups import HasDups, DupLines, CountDups
from .lines.first_line import FirstLine
from .lines.advance import Advance, AdvanceAll
from .lines.after_blank import AfterBlank
from .variables.variables import Variables
from .variables.pushpop import Push, PushDistinct, Pop, Peek, PeekSize, Stack
from .variables.get import Get
from .variables.put import Put
from .variables.track import Track
from .misc.random import Random, Shuffle
from .misc.importf import Import
from .misc.fingerprint import LineFingerprint, StoreFingerprint, FileFingerprint
from .testing.debug import Debug, BriefStackTrace, VoteStack, DoWhenStack, Log
from .validity.line import Line
from .validity.failed import Failed
from .validity.fail import Fail, FailAll
from .types.nonef import Nonef, Blank, Wildcard
from .types.decimal import Decimal
from .types.boolean import Boolean
from .types.datef import Date
from .types.email import Email
from .types.url import Url
from .types.string import String


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
    MY_FUNCTIONS = {}

    @classmethod
    def add_function(cls, name: str, function: Function) -> None:
        """use to add a new, external function at runtime"""
        if name is None:
            name = function.name
        if name is None:
            raise InvalidNameException("Name of function cannot be None")
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
        if name is None or name.strip() == "":
            raise ValueError("Name cannot be None or empty")
        if child and not isinstance(child, Matchable):
            raise InvalidChildException(f"{child} is not a valid child")
        f = None
        qname = name
        name, qualifier = cls.get_name_and_qualifier(name)
        if len(cls.MY_FUNCTIONS) == 0:
            cls.load()
        if name in cls.MY_FUNCTIONS:
            c = cls.MY_FUNCTIONS.get(name)
            f = c(matcher, name, child)
        if f is None and find_external_functions:
            if FunctionFinder.EXTERNALS not in FunctionFactory.NOT_MY_FUNCTION:
                FunctionFinder().load(matcher, cls)
            if name in FunctionFactory.NOT_MY_FUNCTION:
                f = cls.NOT_MY_FUNCTION[name]
                f = f(matcher, name, child)
        if f is None and not find_external_functions:
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

    @classmethod
    def load(cls) -> None:
        fs = {}
        fs["count"] = Count
        fs["has_matches"] = HasMatches
        fs["length"] = Length
        #
        # not aliases
        #
        fs["regex"] = Regex
        fs["exact"] = Regex
        fs["not"] = Not
        #
        # not aliases
        #
        fs["now"] = Now
        fs["thisyear"] = Now
        fs["thismonth"] = Now
        fs["today"] = Now
        fs["in"] = In
        fs["concat"] = Concat
        #
        # not aliases
        #
        fs["contains"] = Contains
        fs["find"] = Contains
        fs["lower"] = Lower
        fs["upper"] = Upper
        fs["caps"] = Capitalize
        fs["alter"] = Alter
        fs["percent"] = Percent
        #
        # aliases
        #
        fs["below"] = AboveBelow
        fs["lt"] = AboveBelow
        fs["before"] = AboveBelow
        fs["lte"] = AboveBelow
        fs["le"] = AboveBelow
        fs["above"] = AboveBelow
        fs["gt"] = AboveBelow
        fs["after"] = AboveBelow
        fs["gte"] = AboveBelow
        fs["ge"] = AboveBelow
        #
        fs["first"] = First
        #
        # aliases
        #
        fs["firstline"] = FirstLine
        fs["firstmatch"] = FirstLine
        fs["firstscan"] = FirstLine
        fs["first_line"] = FirstLine
        fs["first_scan"] = FirstLine
        fs["first_match"] = FirstLine
        fs["count_lines"] = CountLines
        fs["count_scans"] = CountScans
        fs["or"] = Or
        #
        # aliases
        #
        fs["no"] = No
        fs["false"] = No
        fs["yes"] = Yes
        fs["true"] = Yes
        #
        fs["max"] = Max
        fs["min"] = Min
        fs["average"] = Average
        fs["median"] = Median
        fs["random"] = Random
        fs["shuffle"] = Shuffle
        #
        # not aliases
        #
        fs["decimal"] = Decimal
        fs["integer"] = Decimal
        fs["end"] = End
        fs["length"] = Length
        fs["add"] = Add
        fs["string"] = String
        fs["boolean"] = Boolean
        #
        # aliases
        #
        fs["subtract"] = Subtract
        fs["minus"] = Subtract
        fs["multiply"] = Multiply
        fs["divide"] = Divide
        fs["tally"] = Tally
        fs["every"] = Every
        #
        # not aliases
        #
        fs["print"] = Print
        fs["error"] = Print
        fs["increment"] = Increment
        #
        # not aliases
        #
        fs["header_name"] = HeaderName
        fs["header_index"] = HeaderName
        fs["header_names_mismatch"] = HeaderNamesMismatch
        fs["substring"] = Substring
        #
        # not aliases
        #
        fs["stop"] = Stop
        fs["fail_and_stop"] = Stop
        fs["stop_all"] = StopAll
        fs["variables"] = Variables
        fs["headers"] = Headers
        fs["any"] = Any
        fs["none"] = Nonef
        #
        # aliases
        #
        fs["blank"] = Blank
        fs["nonspecific"] = Blank
        fs["unspecified"] = Blank
        fs["wildcard"] = Wildcard
        fs["line"] = Line
        fs["last"] = Last
        fs["exists"] = Exists
        fs["mod"] = Mod
        #
        # aliases
        #
        fs["equals"] = Equals
        fs["equal"] = Equals
        fs["eq"] = Equals
        fs["not_equal_to"] = Equals
        fs["neq"] = Equals
        #
        fs["strip"] = Strip
        fs["jinja"] = Jinjaf
        #
        # not aliases
        #
        fs["count_headers"] = CountHeaders
        fs["count_headers_in_line"] = CountHeaders
        fs["percent_unique"] = PercentUnique
        fs["missing"] = All
        fs["all"] = All
        fs["total_lines"] = TotalLines
        fs["push"] = Push
        fs["push_distinct"] = PushDistinct
        fs["pop"] = Pop
        fs["peek"] = Peek
        #
        # aliases
        #
        fs["peek_size"] = PeekSize
        fs["size"] = PeekSize
        #
        # not aliases
        #
        fs["date"] = Date
        fs["datetime"] = Date
        #
        # not aliases
        #
        fs["fail"] = Fail
        fs["fail_all"] = FailAll
        #
        # not aliases
        #
        fs["failed"] = Failed
        fs["valid"] = Failed
        fs["stack"] = Stack
        #
        # not aliases
        #
        fs["stdev"] = Stdev
        fs["pstdev"] = Stdev
        fs["has_dups"] = HasDups
        fs["count_dups"] = CountDups
        fs["dup_lines"] = DupLines
        fs["empty"] = Empty
        fs["advance"] = Advance
        fs["advance_all"] = AdvanceAll
        fs["collect"] = Collect
        fs["replace"] = Replace
        fs["append"] = Append
        fs["insert"] = Insert
        fs["int"] = Int
        fs["float"] = Float
        fs["and"] = And
        fs["track"] = Track
        fs["sum"] = Sum
        #
        # not aliases
        #
        fs["odd"] = Odd
        fs["even"] = Odd
        fs["email"] = Email
        fs["url"] = Url
        fs["subtotal"] = Subtotal
        fs["reset_headers"] = ResetHeaders
        #
        # aliases
        #
        fs["starts_with"] = StartsWith
        fs["startswith"] = StartsWith
        fs["ends_with"] = StartsWith
        fs["endswith"] = StartsWith
        #
        # not aliases
        #
        fs["skip"] = Skip
        fs["take"] = Skip
        fs["skip_all"] = SkipAll
        fs["mismatch"] = Mismatch
        fs["line_number"] = LineNumber
        fs["after_blank"] = AfterBlank
        fs["round"] = Round
        fs["import"] = Import
        fs["print_line"] = PrintLine
        fs["print_queue"] = PrintQueue
        #
        # not aliases
        #
        fs["min_length"] = MinMaxLength
        fs["max_length"] = MinMaxLength
        #
        # not aliases
        #
        fs["too_long"] = MinMaxLength
        fs["too_short"] = MinMaxLength
        #
        # aliases
        #
        fs["between"] = Between
        fs["inside"] = Between
        fs["from_to"] = Between
        fs["range"] = Between
        fs["beyond"] = Between
        fs["outside"] = Between
        fs["before_after"] = Between
        #
        fs["get"] = Get
        fs["put"] = Put
        fs["debug"] = Debug
        fs["log"] = Log
        fs["brief_stack_trace"] = BriefStackTrace
        fs["vote_stack"] = VoteStack
        fs["do_when_stack"] = DoWhenStack
        fs["when_do_stack"] = DoWhenStack
        fs["metaphone"] = Metaphone
        fs["header_table"] = HeaderTable
        fs["row_table"] = RowTable
        fs["var_table"] = VarTable
        fs["run_table"] = RunTable
        fs["empty_stack"] = EmptyStack
        fs["line_fingerprint"] = LineFingerprint
        fs["file_fingerprint"] = FileFingerprint
        fs["store_line_fingerprint"] = StoreFingerprint
        fs["count_bytes"] = CountBytes
        fs["counter"] = Counter
        cls.MY_FUNCTIONS = fs
