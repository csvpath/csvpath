"""too_long(), too_short(), min_length() and max_length().

The boundary, as David put it (2026-11-18): the sentence form is "a value
that is N is too long for this field", so too_long(@n, 5) is True when @n is
5 or more characters, and @n must be 4 or fewer to pass. too_short is the
mirror: too_short(@n, 5) is True when @n is 5 or fewer characters.
min_length() tests the same thing as too_long() (at least N), and
max_length() the same as too_short() (at most N).

These functions used to override to_value(), which skipped the standard
path: onmatch was ignored, and a None reached len() as a raw TypeError.

All cases run on line 1 of test.csv: David Kermit.
"""

import os
import pytest
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"

AT_LEAST = ["too_long", "min_length"]
AT_MOST = ["too_short", "max_length"]


def _run(*, expression: str, mode: str = "raise") -> CsvPath:
    path = CsvPath()
    path.config.add_to_config("errors", "csvpath", mode)
    path.parse(f"${PATH}[1][ {expression} ]")
    path.collect()
    return path


@pytest.mark.parametrize("name", AT_LEAST)
@pytest.mark.parametrize("text,expected", [("abcd", False), ("abcde", True), ("abcdef", True), ("", False)])
def test_at_least_boundary(name, text, expected):
    path = _run(expression=f'@r = {name}("{text}", 5)')
    assert path.variables["r"] is expected


@pytest.mark.parametrize("name", AT_MOST)
@pytest.mark.parametrize("text,expected", [("abcd", True), ("abcde", True), ("abcdef", False), ("", True)])
def test_at_most_boundary(name, text, expected):
    path = _run(expression=f'@r = {name}("{text}", 5)')
    assert path.variables["r"] is expected


def test_too_long_on_a_header():
    # #firstname is "David", 5 characters
    assert _run(expression="@r = too_long(#firstname, 5)").variables["r"] is True
    assert _run(expression="@r = too_long(#firstname, 6)").variables["r"] is False
    assert _run(expression="@r = too_short(#firstname, 5)").variables["r"] is True
    assert _run(expression="@r = too_short(#firstname, 4)").variables["r"] is False


@pytest.mark.parametrize("name", AT_LEAST + AT_MOST)
def test_onmatch_does_not_act_without_a_match(name):
    path = _run(expression=f'@r = {name}.onmatch("abcde", 5) no()')
    assert path.variables.get("r") is None


@pytest.mark.parametrize("name", AT_LEAST + AT_MOST)
def test_onmatch_acts_with_a_match(name):
    path = _run(expression=f'@r = {name}.onmatch("abcde", 5) yes()')
    assert path.variables["r"] is True


@pytest.mark.parametrize("name", AT_LEAST + AT_MOST)
@pytest.mark.parametrize("arg", ["none()", "@never_set", "#5"])
def test_none_raises_a_match_exception_in_raise_mode(name, arg):
    # None is not a declared actual for argument 1. it used to reach len()
    # and escape as a raw TypeError.
    for expression in [f"{name}({arg}, 5)", f"@r = {name}({arg}, 5)"]:
        with pytest.raises(MatchException):
            _run(expression=expression)


@pytest.mark.parametrize("name", AT_LEAST + AT_MOST)
def test_none_is_one_error_in_collect_mode(name):
    path = _run(expression=f"{name}(none(), 5)", mode="collect")
    assert len(path.errors) == 1
    assert "requires a value" in path.errors[0].message
