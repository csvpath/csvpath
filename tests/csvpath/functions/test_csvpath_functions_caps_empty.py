"""caps() on empty values and empty words.

caps() took v[0] and w[0], so "" (or whitespace, which arrives trimmed) and
the empty word between two spaces raised IndexError ("string index out of
range"). "" is a valid str argument, so it must come back as "".
"""

import os

import pytest

from csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


def _value(expression: str):
    path = CsvPath()
    path.parse(f"~ validation-mode: raise, no-print ~ ${PATH}[1][ @r = {expression} ]")
    path.fast_forward()
    return path.variables["r"]


@pytest.mark.parametrize(
    "expression,expected",
    [
        ('caps("")', ""),
        ('caps("  ")', ""),
        ('caps("", yes())', ""),
        ('caps("ab  cd", yes())', "Ab  Cd"),
        ('caps(" ab cd ", yes())', "Ab Cd"),
        ('caps("ab cd", yes())', "Ab Cd"),
        ('caps("ab cd")', "Ab cd"),
        ('caps("a")', "A"),
    ],
)
def test_caps(expression, expected):
    assert _value(expression) == expected


def test_bare_caps_of_empty_matches():
    #
    # the value is "", not None, so caps() matches
    #
    path = CsvPath()
    path.parse(f'~ validation-mode: raise, no-print ~ ${PATH}[1][ caps("") ]')
    assert len(path.collect()) == 1
