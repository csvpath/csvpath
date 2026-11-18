"""gt()/gte()/lt()/lte() and their aliases with None on both sides.

docs/functions/above.md: "The result of comparing None ... is False ...
because there is no ordinal relationship between the two things being
compared." None against a value was already False. None against None fell
through to float(None) and raised TypeError: in a match it failed the line
with an error, and as a value it was silently None. Now it is False, with
no error, in every mode.

test.csv has a header row and 8 data lines.
"""

import os
import pytest
from csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"

NAMES = ["gt", "gte", "ge", "above", "after", "lt", "lte", "le", "below", "before"]


def _path(mode: str) -> CsvPath:
    path = CsvPath()
    path.config.add_to_config("errors", "csvpath", mode)
    return path


@pytest.mark.parametrize("name", NAMES)
def test_none_none_does_not_match(name):
    path = _path("raise")
    path.parse(f"${PATH}[*][ {name}(none(), none()) ]")
    lines = path.collect()
    assert len(lines) == 0
    assert len(path.errors) == 0


@pytest.mark.parametrize("name", NAMES)
def test_none_none_negated_matches_every_line(name):
    path = _path("raise")
    path.parse(f"${PATH}[*][ not({name}(none(), none())) ]")
    lines = path.collect()
    assert len(lines) == 9


@pytest.mark.parametrize("name", NAMES)
def test_none_none_as_a_value_is_false(name):
    path = _path("collect")
    path.parse(f"${PATH}[1][ @r = {name}(none(), none()) ]")
    path.collect()
    assert path.variables["r"] is False
    assert len(path.errors) == 0


@pytest.mark.parametrize("name", NAMES)
def test_missing_header_and_none_is_false(name):
    # a header past the end of the line reads as None
    path = _path("raise")
    path.parse(f"${PATH}[*][ {name}(#5, none()) ]")
    lines = path.collect()
    assert len(lines) == 0


@pytest.mark.parametrize("name", NAMES)
def test_none_against_a_value_still_false(name):
    path = _path("raise")
    path.parse(f"${PATH}[*][ or({name}(none(), 5), {name}(5, none())) ]")
    lines = path.collect()
    assert len(lines) == 0
