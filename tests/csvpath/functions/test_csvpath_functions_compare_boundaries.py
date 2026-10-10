"""Boundary tests for the comparison functions implemented by AboveBelow
(csvpath/matching/functions/math/above.py): gt, above, after, gte, lt,
below, before, and lte.

Every name is checked for less-than, equal, and greater-than operands of
each value kind AboveBelow compares: numbers (int and float), strings,
dates, and datetimes. The equal case is the one issue #301 found broken:
lt(), below(), and before() behaved as lte().

Datetime cases that issue #312 breaks (time of day ignored) are marked as
strict expected failures. When #312 is fixed they will fail as unexpected
passes; remove the markers then.
"""

import os

import pytest

from csvpath.csvpath import CsvPath

DATES = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}dates.csv"

#
# name -> the Python comparison it must agree with
#
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

#
# kind -> (smaller, larger) as (CsvPath text, Python value)
#
VALUES = {
    "int": (("1", 1), ("2", 2)),
    "float": (("1.5", 1.5), ("2.5", 2.5)),
    "string": (('"apple"', "apple"), ('"banana"', "banana")),
    "date": (
        ('date("2001-10-20", "%Y-%m-%d")', (2001, 10, 20)),
        ('date("2002-10-20", "%Y-%m-%d")', (2002, 10, 20)),
    ),
    #
    # datetimes take their own branch in AboveBelow._try_dates()
    #
    "datetime": (
        ('datetime("2001-10-20 10:00:00", "%Y-%m-%d %H:%M:%S")', (2001, 10, 20, 10)),
        ('datetime("2001-10-20 11:00:00", "%Y-%m-%d %H:%M:%S")', (2001, 10, 20, 11)),
    ),
}

ORDERINGS = {
    "less": (0, 1),
    "equal": (0, 0),
    "greater": (1, 0),
}


def _broken_by_312(*, name: str, kind: str, ordering: str) -> bool:
    #
    # issue #312: two datetimes are compared by date only, so they always
    # compare as equal on the same day. a case is broken exactly when its
    # correct answer differs from the answer for equal operands.
    #
    if kind != "datetime":
        return False
    i, j = ORDERINGS[ordering]
    left = VALUES[kind][i][1]
    right = VALUES[kind][j][1]
    return EXPECTED[name](left, right) != EXPECTED[name](left, left)


def _cases() -> list:
    cases = []
    for name in EXPECTED:
        for kind in VALUES:
            for ordering in ORDERINGS:
                marks = []
                if _broken_by_312(name=name, kind=kind, ordering=ordering):
                    marks.append(
                        pytest.mark.xfail(
                            strict=True,
                            reason="#312: datetime comparisons ignore time of day",
                        )
                    )
                cases.append(
                    pytest.param(
                        name,
                        kind,
                        ordering,
                        marks=marks,
                        id=f"{name}-{kind}-{ordering}",
                    )
                )
    return cases


@pytest.mark.parametrize("name,kind,ordering", _cases())
def test_function_compare_boundaries(name: str, kind: str, ordering: str) -> None:
    i, j = ORDERINGS[ordering]
    left_text, left = VALUES[kind][i]
    right_text, right = VALUES[kind][j]
    path = CsvPath()
    path.config.add_to_config("errors", "csvpath", "raise")
    path.parse(f"${DATES}[1][ @r = {name}( {left_text}, {right_text} ) ]")
    path.fast_forward()
    assert path.variables["r"] is EXPECTED[name](left, right)
