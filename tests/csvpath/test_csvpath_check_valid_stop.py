"""Language errors and validation failures in check_valid() (#343).

- A language error is reported where it is found. In no-raise mode the run
  continues; in raise mode it raises. blank() outside line() used to raise
  without reporting, so in no-raise mode the error vanished: no error, no
  printout, and a valid run.
- An exception that escapes a match component's check_valid() means
  validation itself failed. Expression reports it and stops the run.
  Expression.check_valid() used to set matcher.stopped, which nothing
  reads, so the run went on with a half-built expression.
"""

import contextlib
import io
import os

import pytest

from csvpath import CsvPath
from csvpath.matching.functions.boolean.yes import Yes
from csvpath.matching.util.exceptions import ChildrenException

TEST_CSV = os.path.join("tests", "csvpath", "test_resources", "test.csv")
NO_RAISE = "print, no-raise, fail, collect"
DATA_LINES = [1, 2, 3, 4, 5, 6, 7, 8]


def _run(*, body: str, mode: str = NO_RAISE):
    path = CsvPath()
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        path.parse(f"~ validation-mode: {mode} ~ ${TEST_CSV}[1*][ {body} ]")
        lines = path.collect()
    return path, lines, out.getvalue()


#
# blank() outside line(): a reported language error
#


def test_check_valid_blank_outside_line_is_reported() -> None:
    path, _, out = _run(body='blank(#firstname) push("seen", line_number())')
    messages = [e.message for e in path.errors]
    assert messages == ["Blank can only be used within a line schema"]
    assert "Blank can only be used within a line schema" in out
    assert path.is_valid is False


def test_check_valid_blank_outside_line_run_continues() -> None:
    #
    # like other reported language errors in no-raise mode
    #
    path, _, _ = _run(body='blank(#firstname) push("seen", line_number())')
    assert path.variables["seen"] == DATA_LINES
    assert path.stopped is False


def test_check_valid_blank_outside_line_raise_mode() -> None:
    with pytest.raises(ChildrenException, match="within a line schema"):
        _run(body="blank(#firstname)", mode="print, raise")


def test_check_valid_blank_inside_line_unaffected() -> None:
    path, lines, _ = _run(
        body="line(string(#firstname), string(#lastname), blank(#say))"
    )
    assert path.errors_count == 0
    assert path.is_valid is True
    assert len(lines) == len(DATA_LINES)


def test_check_valid_line_language_error_run_continues() -> None:
    path, _, _ = _run(
        body='line(string(#firstname), count()) push("seen", line_number())'
    )
    assert path.is_valid is False
    assert path.variables["seen"] == DATA_LINES
    assert path.stopped is False


#
# validation itself fails: the run stops
#


@pytest.fixture
def broken_yes(monkeypatch):
    def check_valid(self):
        raise RuntimeError("validation blew up")

    monkeypatch.setattr(Yes, "check_valid", check_valid)


def test_check_valid_failure_stops_the_run(broken_yes) -> None:
    path, lines, out = _run(body='yes() push("seen", line_number())')
    assert path.stopped is True
    #
    # no expression ran on any line
    #
    assert "seen" not in path.variables
    assert lines == []
    assert [e.message for e in path.errors] == ["validation blew up"]
    assert "validation blew up" in out
    assert path.is_valid is False


def test_check_valid_failure_raise_mode(broken_yes) -> None:
    with pytest.raises(RuntimeError, match="validation blew up"):
        _run(body='yes() push("seen", line_number())', mode="print, raise")
