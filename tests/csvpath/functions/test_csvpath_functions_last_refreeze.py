"""Match components after a last() when/do, or after last(<function>), still
run on the last line (issue #324).

Both unfroze the path to run their action and then set it to frozen
unconditionally. On an ordinary last line that froze every match component
after them, so checks were silently skipped and an invalid last line could
be accepted. They now restore the frozen state they found, so a blank last
line, which is frozen, stays frozen.

Data, column a:

    line 0  a     (header)
    line 1  x
    line 2  y     the last line; "y" fails eq(#a, "x")
"""

import pytest

from csvpath import CsvPath

DATA = "a\nx\ny\n"
BLANK_END = "a\nx\ny\n\n"


def _run(*, tmp_path, scan: str, match: str, text: str = DATA) -> CsvPath:
    data = tmp_path / "data.csv"
    data.write_text(text, encoding="utf-8")
    path = CsvPath()
    path.collect(f"~ validation-mode: print, no-raise ~ ${data}[{scan}][ {match} ]")
    return path


def _ids(*, tmp_path, scan: str, match: str) -> list[str]:
    data = tmp_path / "data.csv"
    data.write_text(DATA, encoding="utf-8")
    path = CsvPath()
    lines = path.collect(
        f"~ validation-mode: print, no-raise ~ ${data}[{scan}][ {match} ]"
    )
    return [line[0] for line in lines]


@pytest.mark.parametrize(
    "match,expected",
    [
        ('last.nocontrib() -> print("done")  eq(#a, "x")', ["x"]),
        ('last.nocontrib() -> print("done")  integer.notnone(#a)', []),
        ('last.nocontrib() -> fail()  eq(#a, "x")', ["x"]),
        #
        # last() is not nocontrib here, so line 1 fails on last() itself;
        # line 2 must still fail eq()
        #
        ('last(print("done"))  eq(#a, "x")', []),
        #
        # the order that always worked
        #
        ('eq(#a, "x")  last.nocontrib() -> print("done")', ["x"]),
    ],
)
@pytest.mark.parametrize("scan", ["1*", "*"])
def test_function_last_checks_after_run_on_last_line(
    tmp_path, scan: str, match: str, expected: list
) -> None:
    assert _ids(tmp_path=tmp_path, scan=scan, match=match) == expected


@pytest.mark.parametrize("scan,lines", [("1*", 2), ("*", 3), ("1-1", 1)])
def test_function_last_counter_after_counts_last_line(
    tmp_path, scan: str, lines: int
) -> None:
    path = _run(
        tmp_path=tmp_path,
        scan=scan,
        match='last.nocontrib() -> push("fired", line_number())  counter.n(1)',
    )
    assert path.variables["n"] == lines


def test_function_last_composed_after_when_do_fires(tmp_path) -> None:
    path = _run(
        tmp_path=tmp_path,
        scan="1*",
        match='last.nocontrib() -> print("a")  and.nocontrib( last(), yes() ) -> push("c", line_number())',
    )
    assert path.variables["c"] == [2]


def test_function_last_blank_last_line_stays_frozen(tmp_path) -> None:
    #
    # a blank last line is frozen: only last() and fail() run on it. the
    # when/do unfreezes for its action and must restore frozen afterwards,
    # so the counter after it does not count the blank line.
    #
    path = _run(
        tmp_path=tmp_path,
        scan="*",
        match='last.nocontrib() -> push("fired", line_number())  counter.n(1)',
        text=BLANK_END,
    )
    assert path.variables["fired"] == [3]
    assert path.variables["n"] == 3
