"""CsvPath.completed must be False, not raise, for a csvpath that is
loaded but has not read a line. The run loops save a failed instance's
result before re-raising, and that save asks whether the csvpath
completed; a TypeError there used to replace the real exception.
"""

import os

from csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


def _parsed(scan: str) -> CsvPath:
    path = CsvPath()
    path.parse(f"${PATH}[{scan}][yes()]")
    return path


def test_parsed_but_not_run_has_a_line_monitor_with_no_line():
    path = _parsed("0-3")
    assert path.scanner.to_line == 3
    assert path.line_monitor is not None
    assert path.line_monitor.physical_line_number is None


def test_not_completed_before_any_line_is_read():
    assert _parsed("0-3").completed is False


def test_star_scan_not_completed_before_any_line_is_read():
    #
    # [*] resolves to_line to the last line of the file
    #
    path = _parsed("*")
    assert path.scanner.to_line is not None
    assert path.completed is False


def test_completed_after_a_full_run():
    path = _parsed("0-3")
    path.fast_forward()
    assert path.completed is True
