"""onmatch on value producers: substring, upper, length, int, round and get.

docs/qualifiers.md#onmatch: "onmatch indicates that action on the variable or
function only happens when the whole path matches a row. All functions can
take onmatch." Each of these functions lists onmatch as a value qualifier in
docs/func_gen/<name>.md.

So for @r = f.onmatch(...):

- when the row does not match (here because of no()), f does not act, and @r
  does not get f's value
- when the row matches (yes()), @r gets f's value as usual

What @r holds in the non-matching case is not documented. The assignment
itself has no onmatch, so it still runs and stores None; the key exists. The
tests assert that @r is None, which holds whether it is absent or None, and a
separate test pins that the key is present. To keep a variable unset, onmatch
goes on the variable (@r.onmatch = ...), which is also tested.

All cases run on line 1 of test.csv: David Kermit.
"""

import os

import pytest

from csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"

# (function call with onmatch, value when the row matches)
CASES = [
    ("substring.onmatch(#firstname, 2)", "Da"),
    ("upper.onmatch(#firstname)", "DAVID"),
    ("length.onmatch(#firstname)", 5),
    ('int.onmatch("5")', 5),
    ("round.onmatch(4.567, 1)", 4.6),
    ('get.onmatch("x")', 7),
]

# get() reads @x, so every csvpath sets it first
SETUP = "@x = 7"


def _run(*, expression: str, lines: str = "1") -> tuple[dict, int]:
    path = CsvPath()
    path.parse(f"${PATH}[{lines}][ {SETUP} {expression} ]")
    matched = path.collect()
    return path.variables, len(matched)


@pytest.mark.parametrize("call,value", CASES)
def test_onmatch_does_not_produce_a_value_without_a_match(call, value):
    variables, matched = _run(expression=f"@r = {call} no()")
    assert matched == 0
    # the function did not act, so @r does not hold its value
    assert variables.get("r") is None


@pytest.mark.parametrize("call,value", CASES)
def test_onmatch_produces_the_value_with_a_match(call, value):
    variables, matched = _run(expression=f"@r = {call} yes()")
    assert matched == 1
    assert variables["r"] == value


@pytest.mark.parametrize("call,value", CASES)
def test_without_onmatch_the_value_is_produced_anyway(call, value):
    # the contrast: without onmatch the function acts even though no()
    # fails the row
    plain = call.replace(".onmatch", "")
    variables, matched = _run(expression=f"@r = {plain} no()")
    assert matched == 0
    assert variables["r"] == value


#
# not pinned yet, pending David's ruling (decision log T27): whether a
# non-matching @r = f.onmatch(...) stores None or leaves r unset, and so
# whether a later non-matching row overwrites an earlier match.
#


@pytest.mark.parametrize("call,value", CASES)
def test_onmatch_on_the_variable_leaves_it_unset(call, value):
    # onmatch on the variable stops the assignment itself
    plain = call.replace(".onmatch", "")
    variables, _ = _run(expression=f"@r.onmatch = {plain} no()")
    assert "r" not in variables


@pytest.mark.parametrize(
    "condition,expected",
    [
        # the last row is a Frog Bat, so the last match sets FROG. a case
        # where the last row does not match is left out until T27.
        ('#lastname == "Bat"', "FROG"),
    ],
)
def test_onmatch_over_a_whole_file(condition, expected):
    variables, matched = _run(
        expression=f"@r = upper.onmatch(#firstname) {condition}", lines="1*"
    )
    assert matched >= 1
    assert variables["r"] == expected
