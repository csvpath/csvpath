# pylint: disable=C0114
from csvpath.matching.productions.expression import Matchable
from .function import Function
from .function_finder import FunctionFinder
from .dates.now import Now
from .dates.roll import Roll
from .dates.part import DateFormat
from .dates.part import DatePart
from .strings.format import Format
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
from .headers.headers_stack import HeadersStack
from .headers.header_name import HeaderName
from .headers.header_names_mismatch import HeaderNamesMismatch
from .headers.collect import Collect
from .headers.replace import Replace
from .headers.rename import Rename
from .headers.append import Append
from .headers.insert import Insert
from .headers.headers import Headers
from .headers.empty_stack import EmptyStack
from .headers.mismatch import Mismatch
from .headers.end import End
from .headers.line_before import LineBefore
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
from .lines.dups import HasDups, DupLines, CountDups, Fingerprint
from .lines.first_line import FirstLine
from .lines.advance import Advance, AdvanceAll
from .lines.after_blank import AfterBlank
from .variables.variables import Variables
from .variables.pushpop import Push, PushDistinct, Pop, Peek, PeekSize, Stack
from .variables.get import Get
from .variables.put import Put
from .variables.track import Track
from .variables.clear import Clear
from .variables.index_of import IndexOf
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
from .types.datatype import Datatype
from .xml.xpath import XPath


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
        if not cls.valid_function_name(name):  # name.isalpha():
            raise InvalidNameException(f"Name {name} is not valid")
        if cls.get_function(None, name=name, find_external_functions=False) is not None:
            function.matcher.csvpath.logger.warning(
                "Internal function is overriden by external function: %s", name
            )
            # raise InvalidNameException("Built-in functions cannot be overriden")
        if not isinstance(function, Function):
            # pass as an instance, not a class, for specificity. good to do?
            raise InvalidChildException(
                "Function being registered must be passed as an instance"
            )
        cls.NOT_MY_FUNCTION[name] = function.__class__

    #
    # valid function names start with a letter and contain only letters,
    # numbers, periods, and/or underscores. the grammar allows '.' and '_' at the
    # end of a function name; i don't love that.
    #
    @classmethod
    def valid_function_name(cls, name: str) -> bool:
        if name.isalpha():
            return True
        if not name[0].isalpha():
            return False
        for _ in name[1:]:
            if _.isalnum():
                continue
            if _ == "_":
                continue
            if _ == ".":
                continue
            return False
        return True

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
        #
        # we check externals first, even though they will be infrequent, so that users
        # can override existing functions with updated functionality
        #
        f = cls._get_external_function_if(
            matcher=matcher,
            child=child,
            name=name,
            f=f,
            find_external_functions=find_external_functions,
        )
        if f is None and len(cls.MY_FUNCTIONS) == 0:
            cls.load()
        if f is None and name in cls.MY_FUNCTIONS:
            c = cls.MY_FUNCTIONS.get(name)
            f = c(matcher, name, child)
        if f is None and not find_external_functions:
            return None
        if f is None:
            if matcher is None:
                raise UnknownFunctionException(
                    f"Function {name} not found. Matcher is None. Config path unavailable. Function imports path unavailable."
                )
            else:
                print(f"external functions: {cls.NOT_MY_FUNCTION}")
                raise UnknownFunctionException(
                    f"{name}. Config path: {matcher.csvpath.config.configpath}. Imports: {matcher.csvpath.config.function_imports}"
                )
        if child:
            child.parent = f
        if qualifier:
            f.set_qualifiers(qualifier)
            f.qualified_name = qname
        if f.matcher is None:
            f.matcher = matcher
        return f

    @classmethod
    def clear_to_reload(cls, imports_path: str) -> None:
        e = FunctionFinder.externals_sentinel_from_path(imports_path)
        if e in FunctionFactory.NOT_MY_FUNCTION:
            del FunctionFactory.NOT_MY_FUNCTION[e]

    @classmethod
    def _get_external_function_if(
        cls,
        *,
        f: Function,
        name: str,
        matcher,
        child: Matchable = None,
        find_external_functions: bool = True,
    ) -> Function:
        if f is None and find_external_functions is True:
            e = FunctionFinder.externals_sentinel(matcher)
            if e not in FunctionFactory.NOT_MY_FUNCTION:
                FunctionFinder.load(matcher, cls)
            if name in FunctionFactory.NOT_MY_FUNCTION:
                f = cls.NOT_MY_FUNCTION[name]
                f = f(matcher, name, child)
        return f

    @classmethod
    def load(cls) -> None:
        fs = {}
        fs["count"] = Count
        fs["has_matches"] = HasMatches
        fs["length"] = Length
        fs["regex"] = Regex
        fs["exact"] = Regex
        fs["not"] = Not
        fs["year"] = DatePart
        fs["month"] = DatePart
        fs["day"] = DatePart
        fs["roll"] = Roll
        fs["now"] = Now
        fs["thisyear"] = Now
        fs["thismonth"] = Now
        fs["today"] = Now
        fs["format_date"] = DateFormat
        fs["in"] = In
        fs["concat"] = Concat
        fs["contains"] = Contains
        fs["find"] = Contains
        fs["format"] = Format
        fs["interpolate"] = Format
        fs["lower"] = Lower
        fs["upper"] = Upper
        fs["caps"] = Capitalize
        fs["alter"] = Alter
        fs["percent"] = Percent
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
        fs["first"] = First
        fs["firstline"] = FirstLine
        fs["firstmatch"] = FirstLine
        fs["firstscan"] = FirstLine
        fs["first_line"] = FirstLine
        fs["first_scan"] = FirstLine
        fs["first_match"] = FirstLine
        fs["count_lines"] = CountLines
        fs["count_scans"] = CountScans
        fs["line_before"] = LineBefore
        fs["or"] = Or
        fs["no"] = No
        fs["false"] = No
        fs["yes"] = Yes
        fs["true"] = Yes
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
        fs["datatype"] = Datatype
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
        #
        # HeaderName tests for header_name_mismatch; however, it hasn't been
        # an alias. It's not a bad feature, but the function needs a rewrite.
        #
        # fs["header_name_mismatch"] = HeaderName
        #
        fs["header_names_mismatch"] = HeaderNamesMismatch
        fs["header_names_match"] = HeaderNamesMismatch
        fs["headers_stack"] = HeadersStack
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
        fs["peek_size"] = PeekSize
        fs["size"] = PeekSize
        fs["date"] = Date
        fs["datetime"] = Date
        fs["fail"] = Fail
        fs["fail_all"] = FailAll
        fs["failed"] = Failed
        fs["valid"] = Failed
        fs["stack"] = Stack
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
        fs["rename"] = Rename
        fs["append"] = Append
        fs["insert"] = Insert
        fs["int"] = Int
        fs["float"] = Float
        fs["and"] = And
        fs["track"] = Track
        fs["track_any"] = Track
        fs["clear"] = Clear
        fs["index_of"] = IndexOf
        fs["sum"] = Sum
        fs["odd"] = Odd
        fs["even"] = Odd
        fs["email"] = Email
        fs["url"] = Url
        fs["subtotal"] = Subtotal
        fs["reset_headers"] = ResetHeaders
        fs["starts_with"] = StartsWith
        fs["startswith"] = StartsWith
        fs["ends_with"] = StartsWith
        fs["endswith"] = StartsWith
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
        fs["min_length"] = MinMaxLength
        fs["max_length"] = MinMaxLength
        fs["too_long"] = MinMaxLength
        fs["too_short"] = MinMaxLength
        fs["between"] = Between
        fs["inside"] = Between
        fs["from_to"] = Between
        fs["range"] = Between
        fs["beyond"] = Between
        fs["outside"] = Between
        fs["before_after"] = Between
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
        fs["fingerprint"] = Fingerprint
        fs["line_fingerprint"] = LineFingerprint
        fs["file_fingerprint"] = FileFingerprint
        fs["store_line_fingerprint"] = StoreFingerprint
        fs["count_bytes"] = CountBytes
        fs["counter"] = Counter
        fs["xpath"] = XPath

        cls.MY_FUNCTIONS = fs
