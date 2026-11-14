"""gt(), lt(), gte(), lte() and their aliases compare a currency string like
"$10" as a string, not a number (#576, David 2026-11-14). A numeric
comparison is written explicitly: gt(int(#a), 9).

Before the fix, AboveBelow asked ExpressionUtility.all([a, b], [float, int]),
which goes through to_int() and to_float(). Those strip $, € and £, so
"$10" compared as 10. == and between() already compared it as a string.
"""

import os

import pytest

from csvpath.csvpath import CsvPath
from csvpath.matching.util.expression_utility import ExpressionUtility as exut

CURRENCY = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}currency_compare.csv"

#
# the rows of currency_compare.csv, in order, as (a, b, compare as)
#
ROWS = [
    ("$10", "9", "string"),
    ("€5", "10", "string"),
    ("$10", "$9", "string"),
    ("10", "9", "number"),
    ("9", "10", "number"),
]

EXPECTED = {
    "gt": lambda a, b: a > b,
    "above": lambda a, b: a > b,
    "after": lambda a, b: a > b,
    "gte": lambda a, b: a >= b,
    "lt": lambda a, b: a < b,
    "below": lambda a, b: a < b,
    "before": lambda a, b: a < b,
    "lte": lambda a, b: a <= b,
}


def _expected(name: str) -> list[bool]:
    ret = []
    for a, b, kind in ROWS:
        if kind == "number":
            ret.append(EXPECTED[name](float(a), float(b)))
        else:
            ret.append(EXPECTED[name](a, b))
    return ret


def _run(comparison: str) -> list:
    path = CsvPath()
    path.parse(f"""${CURRENCY}[1*][ push.nocontrib("r", {comparison}) ]""")
    path.collect()
    return path.variables["r"]


class TestCsvPathFunctionsCompareCurrency:
    @pytest.mark.parametrize("name", list(EXPECTED))
    def test_currency_compares_as_a_string(self, name):
        assert _run(f"{name}(#a, #b)") == _expected(name)

    def test_the_rows_tell_string_from_number(self):
        #
        # each currency row must give a different answer as a string than as
        # a number, or the test above could not tell the two apart.
        #
        for a, b, kind in ROWS:
            if kind == "string":
                sa = a.lstrip("$€")
                sb = b.lstrip("$€")
                assert (a > b) != (float(sa) > float(sb)), (a, b)

    def test_int_converts_currency_for_a_numeric_comparison(self):
        #
        # int("$10") == 10, so gt(int(#a), #b) is the numeric comparison.
        #
        assert _run("gt(int(#a), int(#b))") == [True, False, True, True, False]

    def test_float_converts_currency_for_a_numeric_comparison(self):
        assert _run("lt(float(#a), float(#b))") == [False, True, False, False, True]


class TestExpressionUtilityHasCurrencySymbol:
    @pytest.mark.parametrize(
        "value", ["$10", "€5", "£1,000.50", "10 €", "-$3", "$"]
    )
    def test_true(self, value):
        assert exut.has_currency_symbol(value) is True

    @pytest.mark.parametrize("value", ["10", "1,000", "", "abc", 10, 10.5, None, True])
    def test_false(self, value):
        assert exut.has_currency_symbol(value) is False
