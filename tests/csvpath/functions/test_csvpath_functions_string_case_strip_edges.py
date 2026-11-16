"""Edge-case inputs for strip(), upper(), lower() and caps().

What the docs say (docs/func_gen/<name>.md and docs/functions/string_functions.md):

- strip()  trims leading and trailing whitespace
- upper()  upper-cases a string
- lower()  lower-cases a string
- caps()   upper-cases the first letter, or the first letter of each word
           when the optional second argument is True

All four have a data signature of str only. So none() and a number are not
valid inputs, and these tests expect an argument error for them. A number read
from a header is still a str, so it is valid.

string_edge_values.csv has one value per row:

    1  (empty)
    2  "   "                whitespace only
    3  " Kermit the Frog "  surrounding whitespace
    4  42                   a number, read as a str
    5  mIxEd CaSe

caps() with a blank or whitespace-only value is not tested here. It fails
with "string index out of range", which is reported as a finding in the PR
body rather than pinned.
"""

import os

import pytest

from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException

VALUES = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}string_edge_values.csv"

COLLECT = "~ validation-mode: collect, no-raise, no-print ~"
RAISE = "~ validation-mode: raise, no-print ~"

BLANK = 1
WHITESPACE = 2
PADDED = 3
NUMBER = 4
MIXED = 5


def _run(*, expression: str, line: int = BLANK, mode: str = ""):
    """Runs one line in a mode and returns the CsvPath and its collected lines."""
    path = CsvPath()
    path.parse(f"{mode} ${VALUES}[{line}][ {expression} ]")
    lines = path.collect()
    return path, lines


def _result(*, expression: str, line: int = BLANK):
    """Assigns the expression to @result and returns @result. There must be no errors."""
    path, lines = _run(expression=f"@result = {expression}", line=line, mode=COLLECT)
    assert path.errors == [] or path.errors is None
    # a valid string value lets the line match
    assert len(lines) == 1
    return path.variables["result"]


# ---------------------------------------------------------------------------
# header values
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "function,expected",
    [
        ("strip", "Kermit the Frog"),
        ("upper", "KERMIT THE FROG"),
        ("lower", "kermit the frog"),
        ("caps", "Kermit the Frog"),
    ],
)
def test_header_value(function, expected):
    assert _result(expression=f"{function}(#value)", line=PADDED) == expected


@pytest.mark.parametrize(
    "function,expected",
    [
        ("upper", "MIXED CASE"),
        ("lower", "mixed case"),
        # caps() only changes the first letter; the rest keep their case
        ("caps", "MIxEd CaSe"),
    ],
)
def test_header_value_mixed_case(function, expected):
    assert _result(expression=f"{function}(#value)", line=MIXED) == expected


def test_caps_all_words_header_value():
    # with a True second argument every word gets an initial capital
    assert _result(expression="caps(#value, yes())", line=PADDED) == "Kermit The Frog"


# ---------------------------------------------------------------------------
# blank and whitespace-only values
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("function", ["strip", "upper", "lower"])
def test_blank_header_value(function):
    # an empty string is still a str, so it is valid and comes back empty
    assert _result(expression=f"{function}(#value)", line=BLANK) == ""


@pytest.mark.parametrize("function", ["strip", "upper", "lower"])
def test_whitespace_only_header_value(function):
    # for strip() an empty result is documented. For upper() and lower()
    # the docs do not mention trimming, but the value arrives trimmed, so
    # the result is empty too. This pins that current behavior.
    assert _result(expression=f"{function}(#value)", line=WHITESPACE) == ""


def test_strip_trims_a_variable():
    # a variable keeps its whitespace when assigned, so this checks that
    # strip() itself does the trimming
    path, lines = _run(expression='@w = "  x y  " @result = strip(@w)')
    assert path.variables["w"] == "  x y  "
    assert path.variables["result"] == "x y"
    assert len(lines) == 1


def test_strip_whitespace_only_variable():
    path, lines = _run(expression='@w = "   " @result = strip(@w)')
    assert path.variables["w"] == "   "
    assert path.variables["result"] == ""


# ---------------------------------------------------------------------------
# numbers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("function", ["strip", "upper", "lower", "caps"])
def test_number_from_a_header_is_a_string(function):
    # header values are always strings, so "42" is a valid input
    assert _result(expression=f"{function}(#value)", line=NUMBER) == "42"


@pytest.mark.parametrize("function", ["upper", "lower", "caps"])
def test_number_term_is_an_error(function):
    # the data signature is str only, so an int term is an argument error
    path, lines = _run(expression=f"@result = {function}(42)", mode=COLLECT)
    assert lines == []
    assert path.variables.get("result") is None
    messages = [e.message for e in path.errors]
    assert f"{function} requires a string for argument 1" in messages


@pytest.mark.parametrize("function", ["strip", "upper", "lower", "caps"])
def test_number_variable_is_an_error(function):
    # the variable holds an int, not a str
    path, lines = _run(expression=f"@n = 42 @result = {function}(@n)", mode=COLLECT)
    assert lines == []
    messages = [e.message for e in path.errors]
    assert f"{function} requires a string for argument 1" in messages


def test_strip_does_not_accept_a_term():
    # strip()'s call signature, unlike the other three, has no Term
    path, lines = _run(expression="@result = strip(42)", mode=COLLECT)
    assert lines == []
    assert any("arg 1 is an unexpected type" in e.message for e in path.errors)


@pytest.mark.parametrize("function", ["upper", "lower", "caps"])
def test_number_term_raises_in_raise_mode(function):
    path = CsvPath()
    path.parse(f"{RAISE} ${VALUES}[1][ @result = {function}(42) ]")
    with pytest.raises(MatchException, match="requires a string for argument 1"):
        path.fast_forward()


# ---------------------------------------------------------------------------
# none()
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("function", ["strip", "upper", "lower", "caps"])
def test_none_is_an_error(function):
    # None is not in the data signature, so none() is an argument error
    # and not, for example, the string "None"
    path, lines = _run(expression=f"@result = {function}(none())", mode=COLLECT)
    assert lines == []
    assert path.variables.get("result") is None
    messages = [e.message for e in path.errors]
    assert f"{function} requires a value for argument 1" in messages


@pytest.mark.parametrize("function", ["strip", "upper"])
def test_none_variable_is_an_error(function):
    path, lines = _run(
        expression=f"@n = none() @result = {function}(@n)", mode=COLLECT
    )
    assert lines == []
    messages = [e.message for e in path.errors]
    assert f"{function} requires a value for argument 1" in messages


@pytest.mark.parametrize("function", ["strip", "upper"])
def test_none_raises_in_raise_mode(function):
    path = CsvPath()
    path.parse(f"{RAISE} ${VALUES}[1][ @result = {function}(none()) ]")
    with pytest.raises(MatchException, match="requires a value for argument 1"):
        path.fast_forward()
