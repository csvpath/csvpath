import math
import pytest
import unittest
import datetime
from csvpath.csvpath import CsvPath
from csvpath.matching.util.expression_utility import ExpressionUtility
from csvpath.matching.functions.print.printf import Print
from tests.save import Save


class TestExpressionUtil(unittest.TestCase):
    def test_expression_utility_is_one_of(self):
        assert not ExpressionUtility.is_one_of([None], [])
        assert not ExpressionUtility.is_one_of([], [])
        assert not ExpressionUtility.is_one_of({}, [])
        assert not ExpressionUtility.is_one_of(tuple(), [])
        assert ExpressionUtility.is_one_of(True, [bool])
        assert not ExpressionUtility.is_one_of([False], [bool])
        assert not ExpressionUtility.is_one_of([3], [int])
        assert not ExpressionUtility.is_one_of([3], [bool, int])
        # we disallow "" because "" is essentially NULL in CSV
        assert not ExpressionUtility.is_one_of("", [bool, str])
        # instead we treat "" ~= None in this method
        assert ExpressionUtility.is_one_of("", [bool, str, None])
        assert not ExpressionUtility.is_one_of(3, [str])
        assert ExpressionUtility.is_one_of(3, [str, int])
        assert ExpressionUtility.is_one_of(True, [str, int])
        assert ExpressionUtility.is_one_of("3", [str, int])
        assert ExpressionUtility.is_one_of(3.14, [float])
        assert ExpressionUtility.is_one_of("3.14", [float])
        assert ExpressionUtility.is_one_of(3.14, [int, str, bool, float])
        assert ExpressionUtility.is_one_of(3.14, [int, str])
        assert ExpressionUtility.is_one_of("pi", [str])
        assert ExpressionUtility.is_one_of(datetime.datetime.now(), [datetime.date])
        assert ExpressionUtility.is_one_of(datetime.datetime.now(), [datetime.datetime])
        assert not ExpressionUtility.is_one_of(
            datetime.datetime.now(), [str, int, float, bool]
        )
        assert ExpressionUtility.is_one_of([[]], [list])
        assert ExpressionUtility.is_one_of([], [list])
        assert not ExpressionUtility.is_one_of((), [list])
        assert not ExpressionUtility.is_one_of((1), [list])
        assert not ExpressionUtility.is_one_of({}, [list])
        assert not ExpressionUtility.is_one_of((), [list])
        assert ExpressionUtility.is_one_of({"a": "b"}, [dict])
        assert ExpressionUtility.is_one_of((), [tuple, dict, int, str, bool])

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

    def test_expression_utility_get_ancestor1(self):
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
        p = path.matcher.expressions[4][0].children[0].right
        print(f"get ancestor: p {p}")
        fail = p.children[0].right
        print(f"get ancestor: fail {fail}")
        a = ExpressionUtility.get_ancestor(fail, Print)
        assert a is not None
        assert isinstance(a, Print)
        a = ExpressionUtility.get_ancestor(fail, "Print")
        assert a is not None
        assert isinstance(a, Print)

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

    def test_exp_util_chain(self):
        path = CsvPath()
        Save._save(path, "test_validity1")
        path.parse(
            f"""${"tests/test_resources/test.csv"}[*][
                any( length( concat("a", "b")))
            ]"""
        )
        path.fast_forward()
        m = path.matcher
        es = m.expressions[0]
        c = es[0].children[0].children[0].children[0].children[0].children[0]
        chain = ExpressionUtility.my_chain(c)
        print(f"chain: {chain}")
        assert chain == "any.length.concat.a"
        # chain is eqiv to: "Expression.any.length.concat.Equality.a"
