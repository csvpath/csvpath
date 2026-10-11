"""A function given to last() runs only on the last line, also when it is
wrapped in and() or or() (issue #326).

Validating last()'s argument value at match time computed it on every
line; for and() and or(), computing the value runs their children, side
effects and all. last() no longer validates its argument's value, which is
declared Any.

last_blank.csv: lines 0-2 are data, line 3 is blank. Scanned $[0-2], the
last scanned line is line 2.
"""

import os

import pytest

from csvpath import CsvPath

LAST = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}last_blank.csv"


def _run(match: str) -> dict:
    path = CsvPath()
    path.collect(f"${LAST}[0-2][ {match} ]")
    return path.variables


@pytest.mark.parametrize(
    "match",
    [
        'yes() -> last( push("seen", line_number()) )',
        'yes() -> last( and( push("seen", line_number()), yes() ) )',
        'yes() -> last( or( push("seen", line_number()), no() ) )',
        'last.nocontrib( and( push("seen", line_number()), yes() ) )',
    ],
)
def test_function_last_argument_runs_only_on_last_line(match: str) -> None:
    assert _run(match)["seen"] == [2]


@pytest.mark.parametrize(
    "match",
    [
        "yes() -> last( skip() )  @x = line_number()",
        "yes() -> last( and( skip(), yes() ) )  @x = line_number()",
        #
        # the original form of test_function_last_blank_4 in
        # test_csvpath_functions_last.py
        #
        'yes() -> last( and( put("y", "ha"), skip() ) )  @x = line_number()',
    ],
)
def test_function_last_skip_skips_only_last_line(match: str) -> None:
    #
    # skip() on line 2 skips the assignment there, so @x keeps line 1
    #
    assert _run(match)["x"] == 1
