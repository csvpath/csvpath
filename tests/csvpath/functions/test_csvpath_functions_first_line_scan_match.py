"""Which line firstline(), firstscan() and firstmatch(), and their aliases, fire on.

What the docs say (docs/functions/last.md and docs/func_gen/<name>.md):

- firstline() (alias first_line()) is True only for line 0, the header row.
  "If the scan does not start at 0 firstline() will not be seen."
- firstscan() (alias first_scan()) is True on the first line scanned.
- firstmatch() (alias first_match()) is True on the first line where all
  the other match components are True.
- nocontrib on the left-hand side of -> keeps the function from affecting
  whether the row matches (docs/qualifiers.md#nocontrib).

The scan is [3*] over test.csv (lines 0 to 8), and the match condition is
above(line_number(), 4), so the scan starts on line 3 and the first match is
line 5. Each function pushes the line number it fires on.
"""

import os

import pytest

from csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"

# (name, the lines it should fire on)
CASES = [
    # the scan starts at line 3, so line 0 is never seen
    ("firstline", []),
    ("first_line", []),
    # line 3 is the first line scanned
    ("firstscan", [3]),
    ("first_scan", [3]),
    # line 5 is the first line where above(line_number(), 4) is True
    ("firstmatch", [5]),
    ("first_match", [5]),
]


def _run(*, function: str) -> tuple[list, list]:
    path = CsvPath()
    path.parse(
        f"""${PATH}[3*][
            above(line_number(), 4)
            {function}.nocontrib() -> push.nocontrib("fired", line_number())
        ]"""
    )
    lines = path.collect()
    return path.variables.get("fired", []), lines


@pytest.mark.parametrize("function,fired", CASES)
def test_fires_on_line(function, fired):
    seen, _ = _run(function=function)
    assert seen == fired


@pytest.mark.parametrize("function,fired", CASES)
def test_nocontrib_does_not_change_the_matches(function, fired):
    # lines 5 to 8 match whichever function is used, because the function is
    # on the left of -> with nocontrib
    _, lines = _run(function=function)
    assert [line[0] for line in lines] == ["Bird", "Ants", "Slug", "Frog"]


def test_all_three_in_one_csvpath():
    # the same scan with all three in one csvpath, so the lines can be
    # compared side by side
    path = CsvPath()
    path.parse(
        f"""${PATH}[3*][
            above(line_number(), 4)
            firstline.nocontrib() -> push.nocontrib("line", line_number())
            firstscan.nocontrib() -> push.nocontrib("scan", line_number())
            firstmatch.nocontrib() -> push.nocontrib("match", line_number())
        ]"""
    )
    path.collect()
    assert "line" not in path.variables
    assert path.variables["scan"] == [3]
    assert path.variables["match"] == [5]


def test_firstline_fires_on_line_0_when_the_scan_starts_there():
    # the contrast: scanning from 0, firstline() and firstscan() agree
    path = CsvPath()
    path.parse(
        f"""${PATH}[*][
            firstline.nocontrib() -> push.nocontrib("line", line_number())
            firstscan.nocontrib() -> push.nocontrib("scan", line_number())
        ]"""
    )
    path.collect()
    assert path.variables["line"] == [0]
    assert path.variables["scan"] == [0]
