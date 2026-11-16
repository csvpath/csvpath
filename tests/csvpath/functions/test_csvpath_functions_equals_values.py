"""eq(), equals(), equal(), neq() and not_equal_to() on zero-like and missing
values.

A missing value (None or "") never equals a present value. Two missing
values compare as before: None equals None and "" equals "", but "" does not
equal None. Numbers are compared as numbers, so "0", 0, "0.0" and 0.0 are all
equal, as 1 and "1.0" already were.

Before the fix, a truthiness test ran first, so a falsy but real value such as
0 was treated as missing: eq("0", 0) was False. eq(0, none()) raised a
TypeError from float(None).
"""

import os

import pytest

from csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"

#
# (a, b, eq(a, b))
#
CASES = [
    ('"0"', "0", True),
    ("0", '"0.0"', True),
    ('"0"', '"0.0"', True),
    ("0.0", "0", True),
    ("0", "0", True),
    ("1", '"1.0"', True),
    ('""', "0", False),
    ("0", '""', False),
    ("0", "none()", False),
    ("none()", "0", False),
    ("none()", "none()", True),
    ('""', "none()", False),
    ('""', '""', True),
    ('"x"', "0", False),
    ("no()", "0", True),
    ("no()", "no()", True),
    ('"abc"', '"abc"', True),
    ('"abc"', '"abd"', False),
    ('"10"', '"$10"', False),
]

NAMES = {
    "eq": True,
    "equals": True,
    "equal": True,
    "neq": False,
    "not_equal_to": False,
}


def _value(name: str, a: str, b: str):
    path = CsvPath()
    path.parse(f"~ validation-mode: raise, no-print ~ ${PATH}[1][ @r = {name}({a}, {b}) ]")
    path.fast_forward()
    return path.variables["r"]


def _matches(name: str, a: str, b: str) -> bool:
    path = CsvPath()
    path.parse(f"~ validation-mode: raise, no-print ~ ${PATH}[1][ {name}({a}, {b}) ]")
    return len(path.collect()) == 1


class TestCsvPathFunctionsEqualsValues:
    @pytest.mark.parametrize("name", list(NAMES))
    @pytest.mark.parametrize("a,b,equal", CASES)
    def test_value(self, name, a, b, equal):
        expected = equal if NAMES[name] else not equal
        assert _value(name, a, b) is expected

    @pytest.mark.parametrize("name", ["eq", "neq"])
    @pytest.mark.parametrize("a,b,equal", CASES)
    def test_match_agrees_with_value(self, name, a, b, equal):
        expected = equal if NAMES[name] else not equal
        assert _matches(name, a, b) is expected
