"""int() and float() with None, blank and padded input.

docs/functions/intf.md: int() will "Swap a None for 0" and "Strip a string
to empty and treat as 0"; float() converts "similar to the way int() does".
None used to come back as None. notnone still rejects None: it checks the
argument, not the result.
"""

import os
import pytest
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


def _value(expression: str):
    path = CsvPath()
    path.config.add_to_config("errors", "csvpath", "raise")
    path.parse(f"${PATH}[1][ @r = {expression} ]")
    path.fast_forward()
    assert len(path.errors) == 0
    return path.variables["r"]


@pytest.mark.parametrize(
    "expression,expected",
    [
        ("int(none())", 0),
        ('int("")', 0),
        ('int(" ")', 0),
        ('int(" 7 ")', 7),
        ("int(#5)", 0),  # a header past the end of the line reads as None
        ("float(none())", 0.0),
        ('float("")', 0.0),
        ('float(" 2.5 ")', 2.5),
        ("float(#5)", 0.0),
    ],
)
def test_cast_value(expression, expected):
    r = _value(expression)
    assert r == expected
    assert type(r) is type(expected)


def test_int_of_an_unset_variable_is_zero():
    assert _value("int(@never_set)") == 0


def test_int_none_matches():
    # a successful cast is a match, so every line matches
    path = CsvPath()
    path.parse(f"${PATH}[*][ int(none()) ]")
    assert len(path.collect()) == 9


@pytest.mark.parametrize("name", ["int", "float"])
def test_notnone_still_rejects_none(name):
    path = CsvPath()
    path.config.add_to_config("errors", "csvpath", "raise")
    path.parse(f"${PATH}[*][ {name}.notnone(none()) ]")
    with pytest.raises(MatchException):
        path.fast_forward()


def test_arithmetic_on_a_none_cast():
    assert _value("add(int(none()), 3)") == 3
