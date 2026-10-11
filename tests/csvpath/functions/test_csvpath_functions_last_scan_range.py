"""last() fires when no line of the file is in the scan range, and when the
scan's last index is beyond the end of the file (issue #306).

The file's last line is then outside the scan range. Like a blank last
line, it is now given to the matcher frozen, and only last() and
last() -> ... run on it; nothing else runs and the line is not collected
(CsvPath.is_lasts_only_line()).
"""

import pytest

from csvpath import CsvPath

HEADER_ONLY = "a\n"
THREE = "a\nx\ny\n"


def _run(*, tmp_path, text: str, scan: str, match: str) -> tuple[list, CsvPath]:
    data = tmp_path / "data.csv"
    data.write_text(text, encoding="utf-8")
    path = CsvPath()
    lines = path.collect(
        f"~ validation-mode: print, no-raise ~ ${data}[{scan}][ {match} ]"
    )
    return [line[0] for line in lines], path


FIRED = 'last.nocontrib() -> push("fired", line_number())'


@pytest.mark.parametrize(
    "text,scan,fired_at",
    [
        #
        # no line in the scan range
        #
        (HEADER_ONLY, "1*", [0]),
        (HEADER_ONLY, "1", [0]),
        (THREE, "5*", [2]),
        #
        # the scan's last index is beyond the end of the file
        #
        (THREE, "1+3", [2]),
        #
        # regressions: these already fired once, and still fire exactly once
        #
        (THREE, "1-1", [1]),
        (THREE, "*", [2]),
        (THREE, "1*", [2]),
    ],
)
def test_function_last_fires_once(
    tmp_path, text: str, scan: str, fired_at: list
) -> None:
    _, path = _run(tmp_path=tmp_path, text=text, scan=scan, match=FIRED)
    assert path.variables.get("fired") == fired_at


@pytest.mark.parametrize("text,scan", [(HEADER_ONLY, "1*"), (THREE, "5*")])
def test_function_last_fail_fails_with_nothing_scanned(
    tmp_path, text: str, scan: str
) -> None:
    _, path = _run(
        tmp_path=tmp_path, text=text, scan=scan, match="last.nocontrib() -> fail()"
    )
    assert path.is_valid is False


def test_function_last_frozen_line_not_collected_or_counted(tmp_path) -> None:
    #
    # [1+3] scans only line 1 of this file. line 2 is the last line and is
    # outside the scan range: last() fires there, but the line is not
    # collected and the counter does not count it.
    #
    lines, path = _run(
        tmp_path=tmp_path,
        text=THREE,
        scan="1+3",
        match=f"{FIRED}  counter.n(1)",
    )
    assert lines == ["x"]
    assert path.variables["fired"] == [2]
    assert path.variables["n"] == 1


@pytest.mark.parametrize(
    "match",
    [
        "no() -> fail()",
        #
        # the form the ODCS converter emits for a threshold rule
        #
        "and.nocontrib( eq( count_lines(), total_lines() ), gte( @v, 3 ) ) -> fail()",
    ],
)
@pytest.mark.parametrize(
    "text,scan", [(HEADER_ONLY, "1*"), (THREE, "5*"), (THREE, "1+3")]
)
def test_function_last_only_last_runs_on_frozen_last_line(
    tmp_path, text: str, scan: str, match: str
) -> None:
    #
    # on the frozen last line only last() and last() -> ... run, exactly as
    # on a blank last line. a fail() whose condition is not last() must not
    # run there; while frozen, its condition would answer a no-op True.
    #
    _, path = _run(tmp_path=tmp_path, text=text, scan=scan, match=match)
    assert path.is_valid is True
