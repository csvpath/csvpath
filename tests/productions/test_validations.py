import unittest
import pytest
from csvpath.matching.util.exceptions import ChildrenException
from csvpath.matching.productions.variable import Variable
from csvpath.matching.productions.term import Term
from csvpath.matching.productions.header import Header
from csvpath.matching.productions.equality import Equality
from csvpath.matching.functions.boolean.no import No
from csvpath.matching.functions.boolean.inf import In
from csvpath.matching.functions.lines.first import First
from csvpath.matching.functions.lines.stop import Stop
from csvpath.matching.functions.boolean.any import Any
from csvpath.matching.functions.boolean.empty import Empty
from csvpath.matching.functions.math.equals import Equals
from csvpath.matching.functions.headers.end import End
from csvpath.matching.functions.headers.headers import Headers
from csvpath.matching.functions.lines.dups import HasDups
from csvpath.matching.functions.print.printf import Print
from csvpath.matching.functions.strings.regex import Regex
from csvpath import CsvPath

VAR = Variable(None, name="no", value=None)
TERM = Term(None, name=None, value="term")
HEADER = Header(None, name=None, value="header")
HEADERS = Headers(None, name="headers")
FUNC = Stop(None, name="stop")
EQ = Equality(None)


class TestValidations(unittest.TestCase):
    def test_validation_validate_zero_one_or_two_args1(self):
        path = CsvPath()
        path.parse("$tests/test_resources/test.csv[0][yes()]")
        path.fast_forward()
        e = Any(matcher=path.matcher, name="no")
        eq = Equality(None)
        eq.children = [VAR, HEADER]
        eq.op = "=="
        e.children = [eq]
        with pytest.raises(ChildrenException):
            e.check_valid()

    def test_validation_validate_zero_one_or_two_args2(self):
        path = CsvPath()
        path.parse("$tests/test_resources/test.csv[0][yes()]")
        path.fast_forward()
        e = Any(matcher=path.matcher, name="no")
        eq = Equality(None)
        eq.children = [VAR, TERM]
        eq.op = ","
        e.children = [eq]
        with pytest.raises(ChildrenException):
            e.check_valid()

    def test_validation_validate_zero_one_or_two_args4(self):
        path = CsvPath()
        path.parse("$tests/test_resources/test.csv[0][yes()]")
        path.fast_forward()
        e = Any(matcher=path.matcher, name="any")
        eq = Equality(None)
        eq.children = [HEADERS, TERM, TERM]
        eq.op = ","
        e.children = [eq]
        with pytest.raises(ChildrenException):
            e.check_valid()

    def test_validation_validate_one_arg1(self):
        path = CsvPath()
        path.parse("$tests/test_resources/test.csv[0][yes()]")
        path.fast_forward()
        e = Empty(matcher=path.matcher, name="empty")
        e.children = [VAR, TERM]
        with pytest.raises(ChildrenException):
            e.check_valid()

    def test_validation_validate_one_arg2(self):
        path = CsvPath()
        path.parse("$tests/test_resources/test.csv[0][yes()]")
        path.fast_forward()
        e = Empty(path.matcher, name="empty")
        eq = Equality(None)
        eq.children = [VAR, TERM]
        eq.op = ","
        e.children = [eq]
        with pytest.raises(ChildrenException):
            e.check_valid()

    def test_validation_validate_one_or_more_args1(self):
        path = CsvPath()
        path.parse("$tests/test_resources/test.csv[0][yes()]")
        path.fast_forward()
        e = First(path.matcher, name="first")
        eq = Equality(None)
        eq.children = [VAR, TERM]
        eq.op = "="
        e.children = [eq]
        with pytest.raises(ChildrenException):
            e.check_valid()

    # one=term
    # left=term
    # right=fun, eq
    def test_validation_validate_one_or_two_args1(self):
        path = CsvPath()
        path.parse("$tests/test_resources/test.csv[0][yes()]")
        path.fast_forward()
        e = Print(path.matcher, name="print")
        one = Equality(None)
        one.children = [VAR, TERM]
        one.op = "="
        e.children = [one]
        with pytest.raises(ChildrenException):
            e.check_valid()

    def test_validation_validate_one_or_two_args2(self):
        path = CsvPath()
        path.parse("$tests/test_resources/test.csv[0][yes()]")
        path.fast_forward()
        e = Print(path.matcher, name="print")
        e.children = [VAR]
        with pytest.raises(ChildrenException):
            e.check_valid()

    def test_validation_validate_two_args2(self):
        path = CsvPath()
        path.parse("$tests/test_resources/test.csv[0][yes()]")
        path.fast_forward()
        e = Equals(path.matcher, name="print")
        e.children = [VAR]
        with pytest.raises(ChildrenException):
            e.check_valid()

    def test_validation_validate_two_or_three_args2(self):
        path = CsvPath()
        path.parse("$tests/test_resources/test.csv[0][yes()]")
        path.fast_forward()
        e = Regex(path.matcher, name="print")
        e.children = [VAR]
        with pytest.raises(ChildrenException):
            e.check_valid()

    def test_validation_validate_zero_or_more_args1(self):
        path = CsvPath()
        path.parse("$tests/test_resources/test.csv[0][yes()]")
        path.fast_forward()
        e = HasDups(matcher=path.matcher, name="no")
        e.children = [VAR]
        with pytest.raises(ChildrenException):
            e.check_valid()

    def test_validation_validate_zero_or_more_args2(self):
        path = CsvPath()
        path.parse("$tests/test_resources/test.csv[0][yes()]")
        path.fast_forward()
        e = HasDups(matcher=path.matcher, name="no")
        e.children = [VAR, TERM]
        with pytest.raises(ChildrenException):
            e.check_valid()

    def test_validation_validate_zero_or_more_args3(self):
        path = CsvPath()
        path.parse("$tests/test_resources/test.csv[0][yes()]")
        path.fast_forward()
        e = HasDups(matcher=path.matcher, name="no")
        eq = Equality(None)
        eq.children = [VAR, TERM]
        eq.op = "=="
        e.children = [eq]
        with pytest.raises(ChildrenException):
            e.check_valid()

    def test_validation_one1(self):
        path = CsvPath()
        path.parse("$tests/test_resources/test.csv[0][yes()]")
        path.fast_forward()
        v = Empty(matcher=path.matcher, name="no")
        v.children = []
        with pytest.raises(ChildrenException):
            v.check_valid()

    def test_validation_one2(self):
        path = CsvPath()
        path.parse("$tests/test_resources/test.csv[0][yes()]")
        path.fast_forward()
        v = Empty(matcher=path.matcher, name="no")
        v.children = [TERM]
        with pytest.raises(ChildrenException):
            v.check_valid()

    def test_validate_two_or_more_args(self):
        path = CsvPath()
        path.parse("$tests/test_resources/test.csv[0][yes()]")
        path.fast_forward()
        v = In(matcher=path.matcher, name="in")
        EQ.op = ","
        v.children = [EQ]
        # no args, bad
        with pytest.raises(ChildrenException):
            v.check_valid()
            # left only, bad
            EQ.left = VAR
        with pytest.raises(ChildrenException):
            v.check_valid()
            # left term, bad
            EQ.left = TERM
        with pytest.raises(ChildrenException):
            v.check_valid()
            # left var, right equality, bad
            EQ.right = VAR
            EQ.right = TERM
        with pytest.raises(ChildrenException):
            v.check_valid()
            # left equality, right header, bad
            EQ.right = TERM
