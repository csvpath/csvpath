"""in() with a non-string value to find.

Terms in the place-to-look arguments are turned into strings (and split on
"|"). Before this fix the value to find was not, so a number never matched:
in(line_number(), 1, 2) matched no line at all. Now, when the direct
comparison fails, both sides are compared as stripped strings.

test.csv has a header row (line 0) and 8 data lines (1-8).
"""

import os
from csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


def _lines(match_part: str) -> list:
    path = CsvPath()
    path.parse(f"${PATH}[*][ {match_part} ]")
    return path.collect()


def test_in_line_number_with_number_terms():
    lines = _lines("in(line_number(), 1, 2)")
    assert len(lines) == 2
    assert lines[0][0] == "David"
    assert lines[1][0] == "Fish"


def test_in_line_number_with_a_pipe_string():
    lines = _lines('in(line_number(), "1|2|8")')
    assert len(lines) == 3
    assert [line[0] for line in lines] == ["David", "Fish", "Frog"]


def test_in_count_lines_with_a_pipe_string():
    # count_lines() is 1-based over the data lines it has seen
    lines = _lines('in(count_lines(), "3")')
    assert len(lines) == 1


def test_in_number_term_matches_its_string_form():
    # 5 is stringified to "5" on the place-to-look side
    lines = _lines('in(5, "5")')
    assert len(lines) == 9


def test_in_header_strings_unchanged():
    lines = _lines('in(#firstname, "Bug|Bird|Ants")')
    assert len(lines) == 3


def test_in_no_match_stays_false():
    lines = _lines("in(line_number(), 20, 30)")
    assert len(lines) == 0


def test_in_none_does_not_match_the_string_none():
    # None is not stringified: none() is not the text "None"
    lines = _lines('in(none(), "None")')
    assert len(lines) == 0
