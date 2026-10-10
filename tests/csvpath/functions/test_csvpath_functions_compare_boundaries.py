"""Boundary tests for the comparison functions implemented by AboveBelow
(csvpath/matching/functions/math/above.py): gt, above, after, gte, lt,
below, before, and lte.

Every name is checked for less-than, equal, and greater-than operands of
each value kind AboveBelow compares: numbers (int and float), strings,
dates, and datetimes. The equal case is the one issue #301 found broken:
lt(), below(), and before() behaved as lte().

The datetime cases also guard issue #312: datetime comparisons ignored the
time of day, so two datetimes on the same day compared as equal.
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


def _cases() -> list:
    cases = []
    for name in EXPECTED:
        for kind in VALUES:
            for ordering in ORDERINGS:
                cases.append(
                    pytest.param(name, kind, ordering, id=f"{name}-{kind}-{ordering}")
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


@pytest.mark.parametrize(
    "expression,expected",
    [
        #
        # a date compares as midnight against a datetime on the same day.
        # while #312 was open these were all compared by date only, so
        # every one of them read as equal.
        #
        (
            'gt( datetime("2024-01-01 10:00:00", "%Y-%m-%d %H:%M:%S"), date("2024-01-01", "%Y-%m-%d") )',
            True,
        ),
        (
            'lt( date("2024-01-01", "%Y-%m-%d"), datetime("2024-01-01 10:00:00", "%Y-%m-%d %H:%M:%S") )',
            True,
        ),
        (
            'gte( date("2024-01-01", "%Y-%m-%d"), datetime("2024-01-01 10:00:00", "%Y-%m-%d %H:%M:%S") )',
            False,
        ),
        (
            'lte( datetime("2024-01-01 10:00:00", "%Y-%m-%d %H:%M:%S"), date("2024-01-01", "%Y-%m-%d") )',
            False,
        ),
        (
            'gte( datetime("2024-01-01 00:00:00", "%Y-%m-%d %H:%M:%S"), date("2024-01-01", "%Y-%m-%d") )',
            True,
        ),
        (
            'lt( datetime("2024-01-01 00:00:00", "%Y-%m-%d %H:%M:%S"), date("2024-01-01", "%Y-%m-%d") )',
            False,
        ),
    ],
)
def test_function_compare_date_and_datetime(expression: str, expected: bool) -> None:
    path = CsvPath()
    path.config.add_to_config("errors", "csvpath", "raise")
    path.parse(f"${DATES}[1][ @r = {expression} ]")
    path.fast_forward()
    assert path.variables["r"] is expected
