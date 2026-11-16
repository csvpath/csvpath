"""strict allows only numbers (David, 2026-11-15).

integer.strict and decimal.strict accept only an optional leading + or -, the
ASCII digits 0-9, and a "." (required by decimal, refused by integer).
Surrounding whitespace is trimmed. Commas, underscores, exponents, nan, inf,
currency symbols and non-ASCII digits all fail.

Before this change strict leaned on Python's int() / float() and
ExpressionUtility.to_int() / to_float(), so "1,000", "1_000" and "٣" passed.

Without strict nothing changes: integer() and decimal() stay permissive.
"""

import os

import pytest

from csvpath.csvpath import CsvPath
from csvpath.matching.functions.types.decimal import Decimal

NUMBERS = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}strict_numbers.csv"

STRICT = ["5", "-5", "+5", " 5 ", "10.", ".5", "-1.5"]
NOT_STRICT = [
    "1,000",
    "1,000.50",
    "1_000",
    "1e5",
    "nan",
    "inf",
    "٣",
    "--5",
    "5-",
    "1.2.3",
    ".",
    "+",
    "0x10",
    "$10",
    "10 €",
]


def _matched(function: str) -> list[str]:
    path = CsvPath()
    path.parse(
        f"~ validation-mode: no-raise, no-print ~ ${NUMBERS}[1*][ line( {function}(#a) ) ]"
    )
    return [line[0] for line in path.collect()]


class TestDecimalStrictProblem:
    @pytest.mark.parametrize("value", STRICT)
    def test_strict_numbers(self, value):
        assert Decimal._strict_problem(value=value) is None

    @pytest.mark.parametrize("value", NOT_STRICT)
    def test_not_strict_numbers(self, value):
        problem = Decimal._strict_problem(value=value)
        assert problem is not None
        assert problem.startswith(f"'{value}' has 'strict'")

    @pytest.mark.parametrize("value", [5, -5, 10.5, 1e20])
    def test_a_value_that_is_not_a_string_is_already_a_number(self, value):
        #
        # e.g. an int from a variable. str(1e20) is "1e+20", which would fail
        # the character check, so non-strings are not checked.
        #
        assert Decimal._strict_problem(value=value) is None


class TestCsvPathFunctionsStrictNumbers:
    def test_integer_strict(self):
        assert _matched("integer.strict") == ["5", "-5", "+5", " 5 "]

    def test_decimal_strict(self):
        assert _matched("decimal.strict") == ["10.", ".5", "-1.5"]

    def test_integer_is_still_permissive(self):
        assert "1,000" in _matched("integer")
        assert "1_000" in _matched("integer")

    def test_decimal_is_still_permissive(self):
        assert "1,000.50" in _matched("decimal")

    def test_strict_number_variable(self):
        #
        # a number from a variable is not a string, so strict accepts it
        #
        path = CsvPath()
        path.parse(
            f"~ validation-mode: no-raise, no-print ~ ${NUMBERS}[1][ @v = 5 integer.strict(@v) ]"
        )
        assert len(path.collect()) == 1
