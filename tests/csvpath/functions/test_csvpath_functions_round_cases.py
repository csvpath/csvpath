"""Edge cases for round().

docs/func_gen/round.md says round() "Rounds a number, optionally to a certain
number of places". Its data signature accepts None, bool, str, float and int
for the value and an int for the places, and its call signature only accepts a
Term for the places. The docs say nothing about:

- the default number of places
- how a half is rounded
- what none() rounds to
- what happens with a value that is not a number

Tests for those points pin the current behavior and say so in a comment.

round_values.csv holds one value per row, as strings read from a header:

    1  pi          3.14159
    2  negative e  -2.71828
    3  padded      " 1.256 "   surrounding whitespace
    4  word        David       not a number
"""

import os

import pytest

from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"
VALUES = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}round_values.csv"

COLLECT = "~ validation-mode: collect, no-raise, no-print ~"
RAISE = "~ validation-mode: raise, no-print ~"


def _rounded(*, expression: str, file: str = PATH, line: int = 1):
    """Assigns the round() expression to @result on one line and returns it."""
    path = CsvPath()
    path.parse(f"${file}[{line}][ @result = {expression} ]")
    path.fast_forward()
    assert "result" in path.variables
    return path.variables["result"]


@pytest.mark.parametrize(
    "expression,expected",
    [
        ("round(4.4, 0)", 4.0),
        ("round(4.6, 0)", 5.0),
        ("round(0.4, 0)", 0.0),
        ("round(12, 0)", 12.0),
    ],
)
def test_round_zero_places(expression, expected):
    result = _rounded(expression=expression)
    assert result == expected
    # round() converts the value to a float before rounding, so zero
    # places still gives a float, not an int. The docs do not say which
    # type comes back; this pins the current behavior.
    assert isinstance(result, float)


@pytest.mark.parametrize(
    "expression,expected",
    [
        ("round(-4.567, 1)", -4.6),
        ("round(-4.567, 2)", -4.57),
        ("round(-4.4, 0)", -4.0),
        ("round(-4.6, 0)", -5.0),
    ],
)
def test_round_negative_number(expression, expected):
    assert _rounded(expression=expression) == expected


@pytest.mark.parametrize(
    "expression,expected",
    [
        ("round(4.567)", 4.57),
        ("round(-1.234)", -1.23),
        ("round(3)", 3.0),
    ],
)
def test_round_places_omitted_defaults_to_two(expression, expected):
    # the docs say places is optional but do not give a default. The code
    # uses 2 (csvpath/matching/functions/math/round.py). This pins it.
    assert _rounded(expression=expression) == expected


@pytest.mark.parametrize(
    "expression,expected",
    [
        ("round(0.5, 0)", 0.0),
        ("round(1.5, 0)", 2.0),
        ("round(2.5, 0)", 2.0),
        ("round(-2.5, 0)", -2.0),
    ],
)
def test_round_half_goes_to_even(expression, expected):
    # the docs do not say how a half is rounded. round() uses Python's
    # round(), which rounds a half to the nearest even digit. This pins it,
    # so that a change to round-half-up is a deliberate one.
    assert _rounded(expression=expression) == expected


@pytest.mark.parametrize(
    "line,expected",
    [
        (1, 3.14),
        (2, -2.72),
        (3, 1.26),
    ],
)
def test_round_string_number_from_header(line, expected):
    # header values are always strings. the data signature lists str, so a
    # numeric string must round like the number it holds. line 3 has
    # surrounding whitespace, which the float conversion trims.
    assert _rounded(expression="round(#value, 2)", file=VALUES, line=line) == expected


def test_round_quoted_string_term():
    # a quoted term is a str, like a header value
    assert _rounded(expression='round("3.14159", 3)') == 3.142


@pytest.mark.parametrize(
    "expression",
    ["round(none())", "round(none(), 1)"],
)
def test_round_none(expression):
    # the data signature accepts None, but the docs do not say what None
    # rounds to. The value is converted to 0.0. This pins it, pending
    # David's ruling on missing operands in arithmetic (decision log T13);
    # the older round test pins 0 too.
    assert _rounded(expression=expression) == 0.0


def test_round_bad_places_collects_an_error():
    # the docs give places as an int. a non-numeric term is an error
    path = CsvPath()
    path.parse(f'{COLLECT} ${PATH}[1][ @result = round(4.5, "x") ]')
    lines = path.collect()
    messages = [e.message for e in path.errors]
    assert "round requires an integer for argument 2" in messages
    # the error fails the line, and no rounded value is assigned
    assert lines == []
    assert path.variables.get("result") is None


def test_round_bad_places_raises_in_raise_mode():
    path = CsvPath()
    path.parse(f'{RAISE} ${PATH}[1][ @result = round(4.5, "x") ]')
    with pytest.raises(MatchException, match="requires an integer for argument 2"):
        path.fast_forward()


def test_round_variable_places_is_rejected():
    # the call signature only allows a Term for places, so a variable is a
    # language error even when it holds a good int
    path = CsvPath()
    path.parse(f"{COLLECT} ${PATH}[1][ @p = 2 @result = round(4.567, @p) ]")
    lines = path.collect()
    assert lines == []
    assert any("arg 2 is an unexpected type" in e.message for e in path.errors)


def test_round_non_number_header_collects_an_error():
    # the docs do not say what happens with a string that is not a number.
    # The code reports that it cannot convert it. This pins that message.
    path = CsvPath()
    path.parse(f"{COLLECT} ${VALUES}[4][ @result = round(#value) ]")
    lines = path.collect()
    assert lines == []
    assert "Cannot convert David to float" in [e.message for e in path.errors]


def test_round_non_number_header_raises_in_raise_mode():
    path = CsvPath()
    path.parse(f"{RAISE} ${VALUES}[4][ @result = round(#value) ]")
    with pytest.raises(MatchException, match="Cannot convert David to float"):
        path.fast_forward()
