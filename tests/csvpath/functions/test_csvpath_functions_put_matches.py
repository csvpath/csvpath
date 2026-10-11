"""put() matches by default, like the other side-effect functions (issue #328).

put() matched on its value being non-None, but its value is always the
default, None, so a csvpath using put() as a match component matched no
lines. The variable was still set.

test.csv has 9 lines; 7 have lastname Bat.
"""

import os

import pytest

from csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


def _run(match: str) -> tuple[int, dict]:
    path = CsvPath()
    lines = path.collect(f"~ validation-mode: print, no-raise ~ ${PATH}[*][ {match} ]")
    return len(lines), path.variables


@pytest.mark.parametrize(
    "match,lines",
    [
        ('put("y", 1)', 9),
        ('and( put("y", 1), yes() )', 9),
        ('or( put("y", 1), no() )', 9),
        #
        # put() does not vote against the line; the other check decides
        #
        ('put("y", 1)  eq(#lastname, "Bat")', 7),
        #
        # the comparison point: another side-effect function
        #
        ('print("hi")', 9),
    ],
)
def test_function_put_matches_by_default(match: str, lines: int) -> None:
    assert _run(match)[0] == lines


@pytest.mark.parametrize(
    "match,name,value",
    [
        ('put("a")', "a", {}),
        ('put("y", 1)', "y", 1),
        ('put("m", "k", 5)', "m", {"k": 5}),
    ],
)
def test_function_put_still_sets_variables(match: str, name: str, value) -> None:
    lines, variables = _run(match)
    assert lines == 9
    assert variables[name] == value
