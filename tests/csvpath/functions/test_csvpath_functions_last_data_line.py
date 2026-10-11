"""last() is true on the last line that is both scanned and has data (#308).

Trailing blank lines no longer move last(), when blank lines are skipped
(CsvPath.skip_blank_lines, the default). When they are not skipped they are
rows, and last() is true on the last physical line as before. Before, with
blank lines skipped, last() was true on a
trailing blank line, which is processed frozen, so a composed last() such
as and( last(), ... ) -> fail() never ran there: one trailing blank line
silently disabled an end-of-file check.

Each example runs over three versions of the same data, column a with rows
x, y, z (lines 1-3):

    ordinary   the file ends with z
    blank      the file ends with z and then a blank line
    overshoot  the file ends with z, scanned $[2+9]: only line 2 is scanned

@bad counts rows that are not "x".
"""

import pytest

from csvpath import CsvPath

ORDINARY = ("a\nx\ny\nz\n", "1*")
BLANK = ("a\nx\ny\nz\n\n", "1*")
OVERSHOOT = ("a\nx\ny\nz\n", "2+9")
COUNT_BAD = 'not.nocontrib( eq(#a, "x") ) -> counter.bad(1)'


def _run(*, tmp_path, data: tuple, match: str) -> CsvPath:
    text, scan = data
    path_ = tmp_path / "data.csv"
    path_.write_text(text, encoding="utf-8")
    path = CsvPath()
    path.collect(f"~ validation-mode: print, no-raise ~ ${path_}[{scan}][ {match} ]")
    return path


EXAMPLES = [
    ("last() when/do", 'last.nocontrib() -> push("ran", line_number())'),
    ("last() with an argument", 'last.nocontrib( push("ran", line_number()) )'),
    (
        "and( last(), cond )",
        f'{COUNT_BAD}  and.nocontrib( last(), gte( @bad, 1 ) ) -> push("ran", line_number())',
    ),
    (
        "or( last(), no() )",
        'or.nocontrib( last(), no() ) -> push("ran", line_number())',
    ),
]


@pytest.mark.parametrize("name,match", EXAMPLES, ids=[e[0] for e in EXAMPLES])
@pytest.mark.parametrize(
    "data,ran",
    [(ORDINARY, [3]), (BLANK, [3]), (OVERSHOOT, [2])],
    ids=["ordinary", "blank", "overshoot"],
)
def test_function_last_fires_on_last_scanned_data_line(
    tmp_path, data: tuple, ran: list, name: str, match: str
) -> None:
    path = _run(tmp_path=tmp_path, data=data, match=match)
    assert path.variables["ran"] == ran


@pytest.mark.parametrize(
    "data", [ORDINARY, BLANK, OVERSHOOT], ids=["ordinary", "blank", "overshoot"]
)
def test_function_last_end_of_file_check_fails(tmp_path, data: tuple) -> None:
    #
    # the end-of-file check fails the file in every version. before #308 the
    # blank and overshoot versions passed
    #
    path = _run(
        tmp_path=tmp_path,
        data=data,
        match=f"{COUNT_BAD}  and.nocontrib( last(), gte( @bad, 1 ) ) -> fail()",
    )
    assert path.is_valid is False


@pytest.mark.parametrize(
    "data,ran",
    [(ORDINARY, [3]), (BLANK, [3]), (OVERSHOOT, None)],
    ids=["ordinary", "blank", "overshoot"],
)
def test_function_last_condition_reads_last_data_row(
    tmp_path, data: tuple, ran
) -> None:
    #
    # a condition that reads a cell sees the last scanned data row. z is on
    # line 3, which the overshoot scan does not scan
    #
    path = _run(
        tmp_path=tmp_path,
        data=data,
        match='and.nocontrib( last(), eq(#a, "z") ) -> push("ran", line_number())',
    )
    assert path.variables.get("ran") == ran


@pytest.mark.parametrize(
    "data,ran",
    [(ORDINARY, [1, 2]), (BLANK, [1, 2]), (OVERSHOOT, None)],
    ids=["ordinary", "blank", "overshoot"],
)
def test_function_not_last_skips_last_data_row(tmp_path, data: tuple, ran) -> None:
    path = _run(
        tmp_path=tmp_path,
        data=data,
        match='not.nocontrib( last() ) -> push("ran", line_number())',
    )
    assert path.variables.get("ran") == ran


@pytest.mark.parametrize(
    "text,scan,end,completed,stopped",
    [
        ("a\nx\ny\nz\n\n\n", "*", 5, True, False),
        ("a\nx\ny\nz\n\n\n", "1*", 5, True, False),
        ("a\nx\ny\nz\n", "*", 3, True, False),
        ("a\nx\ny\nz\n", "1-2", 3, True, True),
    ],
)
def test_function_last_does_not_change_run_completion(
    tmp_path, text: str, scan: str, end: int, completed: bool, stopped: bool
) -> None:
    #
    # where last() fires is separate from how the run reads and completes:
    # trailing blank lines are still read, the physical end is unchanged, and
    # the run reports completed and stopped as before
    #
    path = _run(
        tmp_path=tmp_path,
        data=(text, scan),
        match='last.nocontrib() -> push("ran", line_number())',
    )
    assert path.line_monitor.physical_end_line_number == end
    assert path.completed is completed
    assert path.stopped is stopped


@pytest.mark.parametrize(
    "skip_blank_lines,fired,counted_at_last",
    [
        #
        # blank lines are skipped, so they are not rows: last() fires on
        # line 2, the last line with data, after both rows are counted
        #
        (True, [2], 2),
        #
        # blank lines are not skipped, so they are rows: last() fires on the
        # last physical line, after every scanned row is counted. the blank
        # last line itself is frozen and not counted, as before #308
        #
        (False, [4], 3),
    ],
)
def test_function_last_follows_skip_blank_lines(
    tmp_path, skip_blank_lines: bool, fired: list, counted_at_last: int
) -> None:
    data = tmp_path / "data.csv"
    data.write_text("id,v\n1,a\n2,b\n\n\n", encoding="utf-8")
    path = CsvPath(skip_blank_lines=skip_blank_lines)
    path.collect(
        f"""~ validation-mode: print, no-raise ~ ${data}[1*][
            counter.seen(1)
            last.nocontrib() -> @at_last = @seen
            last.nocontrib() -> push("fired", line_number())
        ]"""
    )
    assert path.variables["fired"] == fired
    assert path.variables["at_last"] == counted_at_last
    #
    # end-of-run values computed at last() are the final values
    #
    assert path.variables["seen"] == counted_at_last
    assert path.completed is True
