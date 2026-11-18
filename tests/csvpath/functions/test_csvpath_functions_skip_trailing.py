"""A skip() or take() that is the last match component has nothing left
to skip on its line, so it changes nothing there, and it must not cross
into the next line (#478). Before the fix the next line was skipped
entirely: none of its components ran, and a data line was dropped
silently, or, after take(), matched without running."""

import pytest

from csvpath import CsvPath


@pytest.fixture
def four_lines(tmp_path) -> str:
    p = tmp_path / "four_lines.csv"
    p.write_text("a,b\n1,2\n3,4\n5,6\n", encoding="utf-8")
    return str(p)


@pytest.fixture
def two_lines(tmp_path) -> str:
    p = tmp_path / "two_lines.csv"
    p.write_text("a,b\n1,2\n", encoding="utf-8")
    return str(p)


def _run(path: str, body: str) -> tuple[list[str], CsvPath]:
    csvpath = CsvPath()
    csvpath.parse(f"${path}[*][ {body} ]")
    lines = csvpath.collect()
    return [line[0] for line in lines], csvpath


def test_skip_first_still_skips_its_line(four_lines) -> None:
    #
    # correct before the fix too: a skip() with components after it
    #
    matched, p = _run(
        four_lines,
        'first_line.nocontrib() -> skip() push("seen", line_number())',
    )
    assert matched == ["1", "3", "5"]
    assert p.variables["seen"] == [1, 2, 3]


def test_trailing_skip_on_the_first_line(four_lines) -> None:
    matched, p = _run(
        four_lines,
        'push("seen", line_number()) first_line.nocontrib() -> skip()',
    )
    #
    # before the fix: seen [0, 2, 3], matched a, 3, 5 (line 1 dropped)
    #
    assert p.variables["seen"] == [0, 1, 2, 3]
    assert matched == ["a", "1", "3", "5"]


def test_trailing_skip_on_a_middle_line(four_lines) -> None:
    matched, p = _run(
        four_lines,
        'push("seen", line_number()) line_number.nocontrib() == 2 -> skip()',
    )
    #
    # before the fix: seen [0, 1, 2], matched a, 1, 3 (line 3 dropped)
    #
    assert p.variables["seen"] == [0, 1, 2, 3]
    assert matched == ["a", "1", "3", "5"]


def test_trailing_skip_does_not_swallow_last(two_lines) -> None:
    #
    # the leak swallowed the last line, so last() never ran
    #
    _, p = _run(
        two_lines,
        'last.nocontrib() -> @last = "yes" first_line.nocontrib() -> skip()',
    )
    assert p.variables.get("last") == "yes"


def test_trailing_take_does_not_match_the_next_line(four_lines) -> None:
    matched, p = _run(
        four_lines,
        'push("seen", line_number()) #a == "1" line_number.nocontrib() == 1 -> take()',
    )
    #
    # the line that takes is decided by what ran before take(); the next
    # line runs as usual. Before the fix line 2 was matched without its
    # components running
    #
    assert p.variables["seen"] == [0, 1, 2, 3]
    assert matched == ["1"]
