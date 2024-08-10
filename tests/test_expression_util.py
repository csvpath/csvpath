import unittest
from csvpath.csvpath import CsvPath
from csvpath.matching.expression_utility import ExpressionUtility


class TestExpressionUtil(unittest.TestCase):
    def test_bool(self):
        assert ExpressionUtility.asbool(True) is True
        assert ExpressionUtility.asbool(None) is False
        assert ExpressionUtility.asbool("true") is True
        assert ExpressionUtility.asbool("false") is False
        assert ExpressionUtility.asbool("woohoo") is True

    def test_ascomparable(self):
        assert ExpressionUtility.ascompariable(None) is None
        assert ExpressionUtility.ascompariable(True) is True
        assert ExpressionUtility.ascompariable(False) is False
        assert ExpressionUtility.ascompariable("true") is True
        assert ExpressionUtility.ascompariable("false") is False
        assert ExpressionUtility.ascompariable(1) == 1
        assert ExpressionUtility.ascompariable(2.0) == 2.0
        assert ExpressionUtility.ascompariable("-1") == -1

    def test_is_simple_name(self):
        assert ExpressionUtility.is_simple_name("1") is False
        assert ExpressionUtility.is_simple_name("1a") is True
        assert ExpressionUtility.is_simple_name("1.a") is True
        assert ExpressionUtility.is_simple_name("s_._a") is True
        assert ExpressionUtility.is_simple_name("1.os_a") is True
        assert ExpressionUtility.is_simple_name("1@a") is False
        assert ExpressionUtility.is_simple_name("1.a.b") is True

    def test_is_underscored_or_simple(self):
        assert ExpressionUtility._is_underscored_or_simple("1_1") is True
        assert ExpressionUtility._is_underscored_or_simple("1@1") is False
