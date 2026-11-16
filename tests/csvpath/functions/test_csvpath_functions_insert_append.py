"""Tests for insert() and append(): the new header, its index, and the collected lines.

What the docs say (docs/func_gen/insert.md and append.md):

- insert(index, name, data) creates a new header at the 0-based index and sets
  the value for each line of output to the data.
- append(name, value, [add name to header row]) adds the header name and a
  value to the end of every line. The name is added to the headers and can be
  used in the csvpath. When append() is conditional on a when/do, the header
  is in the headers from the first appended line on. The optional third
  argument puts the header name, not the value, into the header row's data.

insert_append.csv:

    a,b,c
    1,2,3
    4,5,6

Every test scans the whole file, so the header row is collected too.

Name collisions with an existing header are not tested here. Both functions
make the line and the headers disagree in length, and insert() with a
header data source at or after the insert index reads the wrong column.
These are reported as findings in the PR body rather than pinned.
"""

import os

import pytest

from csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}insert_append.csv"


def _run(*, expression: str):
    """Collects every line. Returns the CsvPath and the collected lines."""
    path = CsvPath()
    path.parse(f"${PATH}[*][ {expression} ]")
    lines = path.collect()
    return path, lines


# ---------------------------------------------------------------------------
# insert()
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "index,headers",
    [
        (0, ["x", "a", "b", "c"]),
        (1, ["a", "x", "b", "c"]),
        (2, ["a", "b", "x", "c"]),
        (3, ["a", "b", "c", "x"]),
    ],
)
def test_insert_header_index_and_name(index, headers):
    path, _ = _run(expression=f'@v = "X" insert({index}, "x", @v)')
    assert path.headers == headers
    assert path.header_index("x") == index
    assert path.headers[index] == "x"


def test_insert_collected_lines_have_the_new_column():
    path, lines = _run(expression='@v = "X" insert(1, "x", @v)')
    # the header row gets the header name in the new column, and the data
    # rows get the data. The docs do not say what the header row gets; this
    # pins it.
    assert lines == [
        ["a", "x", "b", "c"],
        ["1", "X", "2", "3"],
        ["4", "X", "5", "6"],
    ]


def test_insert_data_from_an_earlier_header():
    # a header before the insert index keeps its position, so its value is
    # copied into the new column on each data row
    path, lines = _run(expression='insert(3, "x", #a)')
    assert lines == [
        ["a", "b", "c", "x"],
        ["1", "2", "3", "1"],
        ["4", "5", "6", "4"],
    ]


def test_insert_the_new_header_is_usable():
    # the inserted header can be read by name later in the csvpath
    path, lines = _run(expression='@v = "X" insert(1, "x", @v) push("seen", #x)')
    # line 0 is the header row, whose data in the new column is the name
    assert path.variables["seen"] == ["x", "X", "X"]


@pytest.mark.parametrize(
    "expression",
    [
        'insert(1, "x", none())',
        '@n = none() insert(1, "x", @n)',
    ],
)
def test_insert_none_value(expression):
    # the data signature accepts None, so the column is added with None
    path, lines = _run(expression=expression)
    assert path.headers == ["a", "x", "b", "c"]
    assert lines == [
        ["a", "x", "b", "c"],
        ["1", None, "2", "3"],
        ["4", None, "5", "6"],
    ]


# ---------------------------------------------------------------------------
# append()
# ---------------------------------------------------------------------------


def test_append_header_index_and_name():
    path, _ = _run(expression='append("x", "v")')
    assert path.headers == ["a", "b", "c", "x"]
    assert path.header_index("x") == 3


def test_append_collected_lines_have_the_new_column():
    # without the third argument, the header row gets the value too
    path, lines = _run(expression='append("x", #a)')
    assert lines == [
        ["a", "b", "c", "a"],
        ["1", "2", "3", "1"],
        ["4", "5", "6", "4"],
    ]


def test_append_header_name_to_header_row():
    # with the third argument True, the header row gets the name
    path, lines = _run(expression='append("x", #a, yes())')
    assert lines == [
        ["a", "b", "c", "x"],
        ["1", "2", "3", "1"],
        ["4", "5", "6", "4"],
    ]


def test_append_the_new_header_is_usable():
    # the docs: "The name is added to the headers and available for use in
    # the csvpath"
    path, lines = _run(expression='append("x", "v", yes()) push("seen", #x)')
    assert path.variables["seen"] == ["x", "v", "v"]


@pytest.mark.parametrize(
    "third,header_row",
    [
        ("", ["a", "b", "c", None]),
        (", yes()", ["a", "b", "c", "x"]),
    ],
)
def test_append_none_value(third, header_row):
    # the data signature accepts None, so the column is added with None
    path, lines = _run(expression=f'append("x", none(){third})')
    assert path.headers == ["a", "b", "c", "x"]
    assert lines == [
        header_row,
        ["1", "2", "3", None],
        ["4", "5", "6", None],
    ]


def test_append_conditional_on_a_when_do():
    # the docs: the header is part of the headers from the first appended
    # line on. Only the line where the when/do fired matches and is collected.
    path, lines = _run(expression='#a == "4" -> append("x", "v")')
    assert path.headers == ["a", "b", "c", "x"]
    assert lines == [["4", "5", "6", "v"]]
