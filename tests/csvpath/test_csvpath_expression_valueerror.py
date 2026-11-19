"""Expression.matches() and a ValueError from a match component (T1).

Expression.matches() used to catch ValueError and only log it: no error
was recorded, raise mode did not raise, and the line matched. David,
2026-11-18: an error a line hits is recorded and the line fails. A
ValueError is now handled like any other exception there.

Function errors are caught earlier, in Function itself. This is the
backstop for any other component, so the tests force one with a
patched Equality.
"""

import os
import pytest
from csvpath import CsvPath
from csvpath.matching.productions import Equality
from csvpath.matching.util.exceptions import MatchException

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


def _raise_value_error(self, *, skip=None):
    raise ValueError("bad data in an equality")


def _path(*, mode: str, csvpath: str) -> CsvPath:
    path = CsvPath()
    path.config.add_to_config("errors", "csvpath", mode)
    path.parse(csvpath)
    return path


def test_collect_mode_records_the_error_and_fails_the_line(monkeypatch):
    monkeypatch.setattr(Equality, "matches", _raise_value_error)
    path = _path(mode="collect", csvpath=f'${PATH}[1][ #firstname == "David" ]')
    assert len(path.collect()) == 0
    assert len(path.errors) == 1
    assert "bad data in an equality" in path.errors[0].message


def test_raise_mode_raises(monkeypatch):
    monkeypatch.setattr(Equality, "matches", _raise_value_error)
    path = _path(mode="raise", csvpath=f'${PATH}[1][ #firstname == "David" ]')
    with pytest.raises(MatchException, match="bad data in an equality") as e:
        path.collect()
    assert isinstance(e.value.__cause__, ValueError)


def test_one_error_per_bad_line(monkeypatch):
    monkeypatch.setattr(Equality, "matches", _raise_value_error)
    path = _path(mode="collect", csvpath=f'${PATH}[1-3][ #firstname == "David" ]')
    assert len(path.collect()) == 0
    assert len(path.errors) == 3


def test_gt_of_a_comma_number_does_not_match():
    # the case that motivated T1: this used to match silently
    path = _path(mode="collect", csvpath=f'${PATH}[1][ gt("1,000", 9999) ]')
    assert len(path.collect()) == 0
    assert len(path.errors) == 1


def test_good_input_is_unchanged():
    path = _path(mode="raise", csvpath=f'${PATH}[1][ #firstname == "David" ]')
    assert len(path.collect()) == 1
    assert len(path.errors) == 0


def test_raise_mode_gt_of_a_comma_number_raises_match_exception():
    path = _path(mode="raise", csvpath=f'${PATH}[1][ gt("1,000", 9999) ]')
    with pytest.raises(MatchException):
        path.collect()
