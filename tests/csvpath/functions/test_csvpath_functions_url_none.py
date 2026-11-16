"""url() treats None as missing, like "" and like email() and uuid().

It used to stringify the value first, so None became "None", failed
validation, and url(none()) did not match even without notnone.
"""

import os

import pytest

from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


def _count(body: str, mode: str = "raise") -> int:
    path = CsvPath()
    path.parse(f"~ validation-mode: {mode}, no-print ~ ${PATH}[1*][ {body} ]")
    return len(path.collect())


@pytest.mark.parametrize("function", ["url", "email", "uuid"])
def test_none_matches_without_notnone(function):
    assert _count(f"{function}(none())") == 8
    assert _count(f"@n = none() {function}(@n)") == 8


def test_notnone_still_rejects_none():
    with pytest.raises(MatchException):
        _count("url.notnone(none())")


@pytest.mark.parametrize(
    "value,matches",
    [("http://example.com", 8), ("not a url", 0), ("", 8)],
)
def test_values_are_unchanged(value, matches):
    assert _count(f'@u = "{value}" url(@u)', mode="no-raise") == matches


def test_notnone_rejects_blank():
    assert _count('@u = "" url.notnone(@u)', mode="no-raise") == 0
