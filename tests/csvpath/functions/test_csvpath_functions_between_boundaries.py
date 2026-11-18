"""Boundary tables for range(), from_to(), inside() and outside(), on numbers, dates and strings.

between() and beyond() are included as the reference names for their aliases.
before_after() is left out: its meaning is undecided (T7).

What docs/functions/between.md says:

- between() or inside() checks if a value is between two other values. In
  contrast to the next line, that is strict: the bounds are not inside.
- from_to() or range() checks if a value is >= the low bound and <= the high
  bound, so the bounds are included.
- beyond() or outside() checks if a value is not between the two values.
- The order of the two comparison values is not important.

The value at the bounds for beyond() and outside() is not tested. "Not
between" with a strict between would make the bounds True, but they are
currently False. That is reported in the PR body rather than pinned.

Each case runs on line 1 of test.csv only.
"""

import os

import pytest

from csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"

# (kind, low, high, below, inside, above), as CVL terms or functions
KINDS = [
    ("numbers", "1", "5", "0", "3", "6"),
    ("strings", '"b"', '"d"', '"a"', '"c"', '"e"'),
    (
        "dates",
        'date("2024-01-01")',
        'date("2024-01-31")',
        'date("2023-12-31")',
        'date("2024-01-15")',
        'date("2024-02-01")',
    ),
]

STRICT = ["between", "inside"]
INCLUSIVE = ["range", "from_to"]
NOT_BETWEEN = ["beyond", "outside"]


def _check(*, function: str, value: str, low: str, high: str) -> bool:
    path = CsvPath()
    path.parse(f"${PATH}[1][ @result = {function}({value}, {low}, {high}) ]")
    path.fast_forward()
    result = path.variables["result"]
    assert isinstance(result, bool)
    return result


def _cases(*, functions: list[str], include_bounds: bool, expected: dict) -> list:
    """Builds (function, kind, position, value, low, high, expected) rows."""
    rows = []
    for function in functions:
        for kind, low, high, below, inside, above in KINDS:
            positions = {"below": below, "inside": inside, "above": above}
            if include_bounds:
                positions["at low"] = low
                positions["at high"] = high
            for position, value in positions.items():
                rows.append(
                    pytest.param(
                        function,
                        value,
                        low,
                        high,
                        expected[position],
                        id=f"{function}-{kind}-{position}",
                    )
                )
    return rows


@pytest.mark.parametrize(
    "function,value,low,high,expected",
    _cases(
        functions=STRICT,
        include_bounds=True,
        expected={
            "below": False,
            "inside": True,
            "above": False,
            # strict: the bounds are not between
            "at low": False,
            "at high": False,
        },
    ),
)
def test_strict_between(function, value, low, high, expected):
    assert _check(function=function, value=value, low=low, high=high) is expected


@pytest.mark.parametrize(
    "function,value,low,high,expected",
    _cases(
        functions=INCLUSIVE,
        include_bounds=True,
        expected={
            "below": False,
            "inside": True,
            "above": False,
            # the docs: >= and <=
            "at low": True,
            "at high": True,
        },
    ),
)
def test_inclusive_range(function, value, low, high, expected):
    assert _check(function=function, value=value, low=low, high=high) is expected


@pytest.mark.parametrize(
    "function,value,low,high,expected",
    _cases(
        functions=NOT_BETWEEN,
        include_bounds=False,
        expected={"below": True, "inside": False, "above": True},
    ),
)
def test_not_between(function, value, low, high, expected):
    assert _check(function=function, value=value, low=low, high=high) is expected


@pytest.mark.parametrize("function", STRICT + INCLUSIVE + NOT_BETWEEN)
@pytest.mark.parametrize("kind,low,high,below,inside,above", KINDS)
def test_order_of_the_bounds_does_not_matter(
    function, kind, low, high, below, inside, above
):
    # the docs: "The order of the two comparison value is not important"
    for value in (below, inside, above):
        forward = _check(function=function, value=value, low=low, high=high)
        reverse = _check(function=function, value=value, low=high, high=low)
        assert forward is reverse, f"{function}({value}) on {kind}"
