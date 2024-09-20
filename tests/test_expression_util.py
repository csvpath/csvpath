import math
import pytest
import unittest
from csvpath.csvpath import CsvPath
from csvpath.matching.util.expression_utility import ExpressionUtility


class TestExpressionUtil(unittest.TestCase):
    def test_exp_util_empty1(self):
        assert ExpressionUtility.is_empty([None])
        assert ExpressionUtility.is_empty([None, None])
        assert ExpressionUtility.is_empty([])
        assert ExpressionUtility.is_empty(())
        assert ExpressionUtility.is_empty((None, None))
        assert ExpressionUtility.is_empty({})
        assert ExpressionUtility.is_empty("")
        assert ExpressionUtility.is_empty([""])
        assert ExpressionUtility.is_empty(None)
        assert ExpressionUtility.is_empty("None")
        assert ExpressionUtility.is_empty(["None"])
        assert not ExpressionUtility.is_empty(["a"])
        assert not ExpressionUtility.is_empty("a")
        assert not ExpressionUtility.is_empty({"a": 1})
        assert not ExpressionUtility.is_empty(("a"))

    def test_expression_utility_my_expression1(self):
        csvpath = """$tests/test_resources/March-2024.csv[*][
                skip( lt(count_headers_in_line(), 9) )
                @header_change = mismatch("signed")
                gt( @header_change, 9) -> reset_headers(print("Resetting headers"))
                print.onchange.once("", skip())

                last.onmatch() ->
                      print("few", fail())

          ]"""
        path = CsvPath()
        path.OR = True
        path.parse(csvpath)
        path.collect()
        last = path.matcher.expressions[4][0].children[0].left
        e = ExpressionUtility.get_my_expression(last)
        assert e == path.matcher.expressions[4][0]

    def test_expression_utility_any_of_my_descendants(self):
        csvpath = """$tests/test_resources/March-2024.csv[*][
                skip( lt(count_headers_in_line(), 9) )
                @header_change = mismatch("signed")
                gt( @header_change, 9) -> reset_headers(print("Resetting headers"))
                print.onchange.once("", skip())

                last.onmatch() ->
                      print("few", fail())

          ]"""
        path = CsvPath()
        path.OR = True
        path.parse(csvpath)
        path.collect()
        last = path.matcher.expressions[4][0].children[0].left
        e = ExpressionUtility.get_my_expression(last)

        assert e == path.matcher.expressions[4][0]
        assert ExpressionUtility.any_of_my_descendants(e, [last])

    def test_exp_util_to_int1(self):
        assert ExpressionUtility.to_int(1) == 1
        assert ExpressionUtility.to_int(1.0) == 1
        assert ExpressionUtility.to_int(None) == 0
        assert ExpressionUtility.to_int(False) == 0
        assert ExpressionUtility.to_int(True) == 1
        assert ExpressionUtility.to_int(" 34 ") == 34
        assert ExpressionUtility.to_int("  ") == 0
        assert ExpressionUtility.to_int("5.01") == 5
        assert ExpressionUtility.to_int("$.01") == 0
        assert ExpressionUtility.to_int("$99.01") == 99
        assert ExpressionUtility.to_int("1,1") == 11
        assert (
            ExpressionUtility.to_int("100,55") == 100
        )  # convert to float() rounds down
        assert ExpressionUtility.to_int("1,550") == 1550

    def test_exp_util_to_int2(self):
        with pytest.raises(ValueError):
            assert ExpressionUtility.to_int(CsvPath()) == 0
        with pytest.raises(ValueError):
            assert ExpressionUtility.to_int("five") == 0

    def test_exp_util_to_float1(self):
        assert ExpressionUtility.to_float(1) == 1.0
        assert ExpressionUtility.to_float(1.0) == 1.0
        assert ExpressionUtility.to_float(None) == 0.0
        assert ExpressionUtility.to_float(False) == 0.0
        assert ExpressionUtility.to_float(True) == 1.0
        assert ExpressionUtility.to_float(" 34 ") == 34.0
        assert ExpressionUtility.to_float("  ") == 0.0
        assert ExpressionUtility.to_float("5.01") == 5.01
        assert ExpressionUtility.to_float("$.01") == 0.01
        assert ExpressionUtility.to_float("$99.01") == 99.01
        assert ExpressionUtility.to_float("1,1") == 11.00
        assert (
            ExpressionUtility.to_float("100,55") == 100.55
        )  # convert to float() rounds down
        assert ExpressionUtility.to_float("1,550") == 1550.00

    def test_exp_util_to_float2(self):
        with pytest.raises(ValueError):
            assert ExpressionUtility.to_float(CsvPath()) == 0
        with pytest.raises(ValueError):
            assert ExpressionUtility.to_float("five") == 0

    def test_exp_util_all(self):
        assert ExpressionUtility.all(None) is False
        assert ExpressionUtility.all([]) is True
        assert ExpressionUtility.all(CsvPath) is True
        assert ExpressionUtility.all(False) is True
        assert ExpressionUtility.all([CsvPath, True]) is False
        assert ExpressionUtility.all([CsvPath, True], classlist=[str, int]) is False
        assert ExpressionUtility.all([CsvPath, True], classlist=(str, int)) is False
        assert ExpressionUtility.all([True, CsvPath], classlist=[bool, int]) is False
        assert (
            ExpressionUtility.all([CsvPath, CsvPath], classlist=[bool, CsvPath])
            is False
        )
        assert ExpressionUtility.all([True, False]) is True

    def test_exp_util_is_none(self):
        assert ExpressionUtility.is_none(None) is True
        assert ExpressionUtility.is_none("None") is True
        assert ExpressionUtility.is_none("nan") is True
        assert ExpressionUtility.is_none("  \t") is True
        assert ExpressionUtility.is_none("\n") is True
        assert ExpressionUtility.is_none("me") is False
        assert ExpressionUtility.is_none(False) is False
        assert ExpressionUtility.is_none([]) is False
        assert ExpressionUtility.is_none(0) is False
        assert ExpressionUtility.is_none(1) is False

    def test_exp_util_bool(self):
        assert ExpressionUtility.asbool(True) is True
        assert ExpressionUtility.asbool(False) is False
        assert ExpressionUtility.asbool(None) is False
        assert ExpressionUtility.asbool("true") is True
        assert ExpressionUtility.asbool("True") is True
        assert ExpressionUtility.asbool("false") is False
        assert ExpressionUtility.asbool("False") is False
        assert ExpressionUtility.asbool("woohoo") is True
        assert ExpressionUtility.asbool("") is False
        assert ExpressionUtility.asbool(1) is True
        assert ExpressionUtility.asbool(0) is False
        assert ExpressionUtility.asbool(-1) is True
        assert ExpressionUtility.asbool([]) is True
        assert ExpressionUtility.asbool({}) is True
        assert ExpressionUtility.asbool(()) is True
        assert ExpressionUtility.asbool(math.nan) is False
        assert ExpressionUtility.asbool("nan") is False
        assert ExpressionUtility.asbool("Nan") is True
        assert ExpressionUtility.asbool("NaN") is False

    def test_exp_util_ascomparable(self):
        assert ExpressionUtility.ascompariable(None) is None
        assert ExpressionUtility.ascompariable(True) is True
        assert ExpressionUtility.ascompariable(False) is False
        assert ExpressionUtility.ascompariable("true") is True
        assert ExpressionUtility.ascompariable("false") is False
        assert ExpressionUtility.ascompariable(1) == 1
        assert ExpressionUtility.ascompariable(2.0) == 2.0
        assert ExpressionUtility.ascompariable("-1") == -1
