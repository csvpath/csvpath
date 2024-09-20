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
from csvpath.matching.functions.lines.dups import HasDups
from csvpath.matching.functions.print.printf import Print
from csvpath.matching.functions.strings.regex import Regex

VAR = Variable(None, name="no", value=None)
TERM = Term(None, name=None, value="term")
HEADER = Header(None, name=None, value="header")
FUNC = Stop(None, name="stop")
EQ = Equality(None)


class TestValidations(unittest.TestCase):
    def test_validation_zero1(self):
        v = No(matcher=None, name="no")
        v.children = [VAR]
        with pytest.raises(ChildrenException):
            v.check_valid()

    def test_validation_zero_or_one1(self):
        e = End(matcher=None, name="no")
        e.children = [VAR, TERM]
        with pytest.raises(ChildrenException):
            e.check_valid()

    def test_validation_zero_or_one2(self):
        e = End(matcher=None, name="no")
        eq = Equality(None)
        eq.children = [VAR, HEADER]
        eq.op = ","
        e.children = [eq]
        with pytest.raises(ChildrenException):
            e.check_valid()

    def test_validation_zero_or_one3(self):
        e = End(matcher=None, name="no")
        e.children = [VAR]
        with pytest.raises(ChildrenException):
            e.check_valid()

    def test_validation_validate_zero_one_or_two_args1(self):
        e = Any(matcher=None, name="no")
        eq = Equality(None)
        eq.children = [VAR, HEADER]
        eq.op = "=="
        e.children = [eq]
        with pytest.raises(ChildrenException):
            e.check_valid()

    def test_validation_validate_zero_one_or_two_args2(self):
        e = Any(matcher=None, name="no")
        eq = Equality(None)
        eq.children = [VAR, TERM]
        eq.op = ","
        e.children = [eq]
        with pytest.raises(ChildrenException):
            e.check_valid()

    def test_validation_validate_zero_one_or_two_args3(self):
        e = Any(matcher=None, name="no")
        e.children = [FUNC]
        with pytest.raises(ChildrenException):
            e.check_valid()

    def test_validation_validate_one_arg1(self):
        e = Empty(None, name="empty")
        e.children = [VAR, TERM]
        with pytest.raises(ChildrenException):
            e.check_valid()

    def test_validation_validate_one_arg2(self):
        e = Empty(None, name="empty")
        eq = Equality(None)
        eq.children = [VAR, TERM]
        eq.op = ","
        e.children = [eq]
        with pytest.raises(ChildrenException):
            e.check_valid()

    def test_validation_validate_one_or_more_args1(self):
        e = First(None, name="first")
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
        e = Print(None, name="print")
        one = Equality(None)
        one.children = [VAR, TERM]
        one.op = "="
        e.children = [one]
        with pytest.raises(ChildrenException):
            e.check_valid()

    def test_validation_validate_one_or_two_args2(self):
        e = Print(None, name="print")
        e.children = [VAR]
        with pytest.raises(ChildrenException):
            e.check_valid()

    def test_validation_validate_two_args1(self):
        e = Equals(None, name="print")
        one = Equality(None)
        one.children = [VAR, TERM]
        one.op = "="
        e.children = [one]
        with pytest.raises(ChildrenException):
            e.check_valid()

    def test_validation_validate_two_args2(self):
        e = Equals(None, name="print")
        e.children = [VAR]
        with pytest.raises(ChildrenException):
            e.check_valid()

    def test_validation_validate_two_or_three_args2(self):
        e = Regex(None, name="print")
        e.children = [VAR]
        with pytest.raises(ChildrenException):
            e.check_valid()

    def test_validation_validate_zero_or_more_args1(self):
        e = HasDups(matcher=None, name="no")
        e.children = [VAR]
        with pytest.raises(ChildrenException):
            e.check_valid()

    def test_validation_validate_zero_or_more_args2(self):
        e = HasDups(matcher=None, name="no")
        e.children = [VAR, TERM]
        with pytest.raises(ChildrenException):
            e.check_valid()

    def test_validation_validate_zero_or_more_args3(self):
        e = HasDups(matcher=None, name="no")
        eq = Equality(None)
        eq.children = [VAR, TERM]
        eq.op = "=="
        e.children = [eq]
        with pytest.raises(ChildrenException):
            e.check_valid()

    def test_validation_one1(self):
        v = Empty(matcher=None, name="no")
        v.children = []
        with pytest.raises(ChildrenException):
            v.check_valid()

    def test_validation_one2(self):
        v = Empty(matcher=None, name="no")
        v.children = [TERM]
        with pytest.raises(ChildrenException):
            v.check_valid()

    def test_validate_two_or_more_args(self):
        v = In(matcher=None, name="in")
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
