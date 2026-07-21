import math
import pytest
import unittest
import os
import datetime
from csvpath.csvpath import CsvPath
from csvpath.matching.util.expression_utility import ExpressionUtility
from csvpath.matching.functions.print.printf import Print

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"
FILE = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}March-2024.csv"


class TestCsvPathExpressionUtil(unittest.TestCase):
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
        csvpath = f"""${FILE}[*][
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
        csvpath = f"""${FILE}[*][
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
        fail = p.children[0].right
        a = ExpressionUtility.get_ancestor(fail, Print)
        assert a is not None
        assert isinstance(a, Print)
        a = ExpressionUtility.get_ancestor(fail, "Print")
        assert a is not None
        assert isinstance(a, Print)

    def test_expression_utility_any_of_my_descendants(self):
        csvpath = f"""${FILE}[*][
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
        assert not isinstance(ExpressionUtility.to_int(CsvPath()), int)
        assert not isinstance(ExpressionUtility.to_int("five"), int)
        assert ExpressionUtility.to_int("five") == "five"

    def test_is_number(self):
        assert ExpressionUtility.is_number(1)
        assert ExpressionUtility.is_number(1.01)
        assert not ExpressionUtility.is_number("")
        assert not ExpressionUtility.is_number(None)
        assert not ExpressionUtility.is_number(True)
        assert not ExpressionUtility.is_number(False)
        assert ExpressionUtility.is_number(-1)
        assert ExpressionUtility.is_number("1,000")
        assert ExpressionUtility.is_number("$1,000.00")
        assert not ExpressionUtility.is_number("no")

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
        assert not isinstance(ExpressionUtility.to_float(CsvPath()), float)
        assert not isinstance(ExpressionUtility.to_float("five"), float)
        assert "five" == ExpressionUtility.to_float("five")

    def test_exp_util_all(self):
        assert ExpressionUtility.all(None) is False
        assert ExpressionUtility.all([]) is True
        assert ExpressionUtility.all(CsvPath) is True
        assert ExpressionUtility.all(False) is True
        assert ExpressionUtility.all([CsvPath, True]) is True
        # this makes no sense!
        # assert ExpressionUtility.all([CsvPath, True]) is False
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

    def test_exp_util_chain_1(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[*][
                any( length( concat("a", "b")))
            ]"""
        )
        path.fast_forward()
        m = path.matcher
        es = m.expressions[0]
        c = es[0].children[0].children[0].children[0].children[0].children[0]
        chain = ExpressionUtility.my_chain(c)
        assert chain == "any[0].length[0].concat[0].a"

    def test_exp_util_chain_2(self):
        path = CsvPath()
        path.parse(
            f"""~ validation-mode:collect,no-raise ~
            ${PATH}[1][
                add("b", "i")
                add("c", subtract("a", "b"))
                add(subtract("g", "h"), subtract("e", "f"))
                in("i", subtract("g", "h"), subtract("e", "f"), subtract("l", "m"), none(), subtract("v", "u"))
            ]"""
        )
        path.fast_forward()
        assert path.errors
        x = [
            "add[0]",
            "add[1].subtract[1]",
            "add[1]",
            "add[2].subtract[0]",
            "add[2].subtract[1]",
            "in[3].subtract[1]",
            "in[3].subtract[2]",
            "in[3].subtract[3]",
            "in[3].subtract[5]",
        ]
        for e in path.errors:
            assert e.source in x
            del x[x.index(e.source)]
        assert len(x) == 0

    def test_exp_util_safe_isinstance(self):
        assert ExpressionUtility.safe_isinstance(1, int)
        assert ExpressionUtility.safe_isinstance(1, (int, str))
        assert not ExpressionUtility.safe_isinstance("1", int)
        # isinstance() raises TypeError for a non-type second arg; safe_isinstance
        # swallows that and returns False rather than propagating
        assert not ExpressionUtility.safe_isinstance(1, "not a type")

    def test_exp_util_isa_none(self):
        assert ExpressionUtility.isa(None, None)
        # None cross-casts to int via to_int(None) == 0, so this is True,
        # not the False you might expect -- documenting actual behavior
        assert ExpressionUtility.isa(None, [int])
        # a non-None obj with no classlist at all has nothing to match against
        assert not ExpressionUtility.isa(1, None)

    def test_exp_util_isa_direct_and_cross_cast(self):
        assert ExpressionUtility.isa(1, (int,))
        assert ExpressionUtility.isa("1", (int,))
        assert ExpressionUtility.isa("1.5", (float,))
        assert ExpressionUtility.isa("true", (bool,))
        assert not ExpressionUtility.isa("", (int,))
        assert ExpressionUtility.isa(datetime.datetime.now(), (datetime.date,))
        assert not ExpressionUtility.isa("not a number", (int,))

    def test_exp_util_isa_classlist_with_instances_not_types(self):
        # non-type entries in classes are converted to their own type()
        assert ExpressionUtility.isa(1, (1,))
        assert not ExpressionUtility.isa(1, ("a string",))

    def test_exp_util_is_date_type(self):
        assert ExpressionUtility.is_date_type(datetime.date(2024, 1, 1))
        assert ExpressionUtility.is_date_type(datetime.datetime(2024, 1, 1))
        assert ExpressionUtility.is_date_type("2024-01-01")
        assert not ExpressionUtility.is_date_type("not a date")
        assert not ExpressionUtility.is_date_type(None)

    def test_exp_util_to_date(self):
        d = datetime.date(2024, 3, 4)
        assert ExpressionUtility.to_date(d) == d
        dt = datetime.datetime(2024, 3, 4, 5, 6, 7)
        assert ExpressionUtility.to_date(dt) == dt.date()
        assert ExpressionUtility.to_date("2024-03-04") == d
        # unparseable input is returned unchanged, not raised
        assert ExpressionUtility.to_date("not a date") == "not a date"
        assert ExpressionUtility.to_date(None) is None

    def test_exp_util_to_datetime(self):
        dt = datetime.datetime(2024, 3, 4, 5, 6, 7)
        assert ExpressionUtility.to_datetime(dt) == dt
        parsed = ExpressionUtility.to_datetime("2024-03-04T05:06:07")
        assert parsed == dt
        assert ExpressionUtility.to_datetime("not a date") == "not a date"
        assert ExpressionUtility.to_datetime(None) is None

    def test_exp_util_is_date_or_datetime_str(self):
        assert ExpressionUtility.is_date_or_datetime_str("2024-03-04") == "date"
        assert (
            ExpressionUtility.is_date_or_datetime_str("2024-03-04T05:06:07")
            == "datetime"
        )
        assert ExpressionUtility.is_date_or_datetime_str("not a date") == "unknown"

    def test_exp_util_is_date_or_datetime_obj(self):
        assert (
            ExpressionUtility.is_date_or_datetime_obj(datetime.date(2024, 3, 4))
            == "date"
        )
        assert (
            ExpressionUtility.is_date_or_datetime_obj(
                datetime.datetime(2024, 3, 4, 0, 0, 0)
            )
            == "date"
        )
        assert (
            ExpressionUtility.is_date_or_datetime_obj(
                datetime.datetime(2024, 3, 4, 5, 6, 7)
            )
            == "datetime"
        )
        assert ExpressionUtility.is_date_or_datetime_obj("not a date/datetime") == "unknown"

    def test_exp_util_to_simple_bool(self):
        assert ExpressionUtility.to_simple_bool(True) is True
        assert ExpressionUtility.to_simple_bool(False) is False
        assert ExpressionUtility.to_simple_bool("true") is True
        assert ExpressionUtility.to_simple_bool("True") is True
        assert ExpressionUtility.to_simple_bool("false") is False
        assert ExpressionUtility.to_simple_bool("False") is False
        # anything else is passed through unchanged, not coerced
        assert ExpressionUtility.to_simple_bool("maybe") == "maybe"
        assert ExpressionUtility.to_simple_bool(3) == 3

    def test_exp_util_numeric_string(self):
        assert ExpressionUtility._numeric_string(1) == "1st"
        assert ExpressionUtility._numeric_string(2) == "2nd"
        assert ExpressionUtility._numeric_string(3) == "3rd"
        assert ExpressionUtility._numeric_string(4) == "4th"
        assert ExpressionUtility._numeric_string(21) == "21st"
        # note: this implementation looks only at the last digit, so 11/12/13
        # come out as "11st"/"12nd"/"13rd" rather than the grammatically
        # correct "11th"/"12th"/"13th" -- documenting actual behavior
        assert ExpressionUtility._numeric_string(11) == "11st"
        assert ExpressionUtility._numeric_string(12) == "12nd"
        assert ExpressionUtility._numeric_string(13) == "13rd"

    def test_exp_util_get_name_and_qualifiers_simple(self):
        name, quals = ExpressionUtility.get_name_and_qualifiers("plain")
        assert name == "plain"
        assert quals == []

    def test_exp_util_get_name_and_qualifiers_dotted(self):
        name, quals = ExpressionUtility.get_name_and_qualifiers("test.onmatch.onchange")
        assert name == "test"
        assert quals == ["onmatch", "onchange"]

    def test_exp_util_get_name_and_qualifiers_quoted(self):
        name, quals = ExpressionUtility.get_name_and_qualifiers('"a.b".onmatch')
        assert name == "a.b"
        assert quals == ["onmatch"]

    def test_exp_util_get_name_and_qualifiers_empty_raises(self):
        with pytest.raises(ValueError):
            ExpressionUtility.get_name_and_qualifiers("")

    def test_exp_util_get_id_and_expressions_index(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[*][
                any( length( concat("a", "b")))
            ]"""
        )
        path.fast_forward()
        m = path.matcher
        es = m.expressions[0]
        top = es[0]
        idx = ExpressionUtility.get_my_expressions_index(top.children[0])
        assert idx == 0
        id1 = ExpressionUtility.get_id(top.children[0])
        id2 = ExpressionUtility.get_id(top.children[0])
        assert id1 == id2
        assert id1.startswith("_intx_")

    def test_exp_util_name_or_class_and_simple_class_name(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[*][
                any( length( concat("a", "b")))
            ]"""
        )
        path.fast_forward()
        m = path.matcher
        es = m.expressions[0]
        any_func = es[0].children[0]
        # equality/expression wrappers are hidden by default
        assert ExpressionUtility.name_or_class(es[0]) == ""
        # a named function shows up with its sibling index
        assert ExpressionUtility.name_or_class(any_func) == "any[0]"
        assert ExpressionUtility.simple_class_name(any_func) == "Any"

    def test_exp_util_descendents(self):
        path = CsvPath()
        path.parse(
            f"""${PATH}[*][
                or( length( concat("a", "b") ), boolean(none()) )
            ]"""
        )
        path.fast_forward()
        m = path.matcher
        es = m.expressions[0]

        print("")
        # find or()
        o = es[0].children[0]
        ds = ExpressionUtility.get_my_descendents(o)
        for i, d in enumerate(ds):
            print(f"ds[{i}]: {d}")
        assert ds
        assert len(ds) == 6
        print("")
        ds = ExpressionUtility.get_my_descendents(o, include_equality=True)
        for i, d in enumerate(ds):
            print(f"ds[{i}]: {d}")

        assert ds
        assert len(ds) == 8
