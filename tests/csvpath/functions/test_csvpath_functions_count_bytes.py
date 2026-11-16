"""Direct tests for count_bytes().

What the docs say:

- docs/func_gen/count_bytes.md: count_bytes() "Returns the total data bytes
  written count. This function is only for named-path group runs. Individual
  CsvPath instances do not write out data, so this value would be 0 for them."
- docs/functions/count_bytes.md: it returns the number of bytes the csvpath
  has written to data.csv. It does not flush first, so it "will commonly give
  numbers that run behind" the bytes directed to be written.

So the documented, deterministic properties are:

- a lone CsvPath always gets 0
- in a named-paths run, the count before anything is written is 0, and the
  count never goes down

count_bytes_utf8.csv has multi-byte UTF-8 values (2, 3 and 4 bytes per
character). Its data.csv, written with \\r\\n line endings, is 45 bytes.

Not asserted here: that the count is at most the bytes really written so far.
The documented "runs behind" allows a lower count, never a higher one, but on
the local backend the count is currently higher. That is reported in the PR
body rather than pinned. The tests below avoid any exact nonzero value for the
same reason.
"""

import os
import uuid

from csvpath import CsvPath
from tests.csvpaths.builder import Builder

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}count_bytes_utf8.csv"

PUSH_COUNTS = '$[*][ push("counts", count_bytes()) ]'


def _group_counts() -> list[int]:
    """Runs PUSH_COUNTS in a one-csvpath named-paths group and returns the counts."""
    # a unique name keeps this run's results apart from every other run
    name = f"count_bytes_{uuid.uuid4().hex}"
    paths = Builder().build()
    paths.file_manager.add_named_file(name=name, path=PATH)
    paths.paths_manager.add_named_paths(name=name, paths=[f"~ id: one ~ {PUSH_COUNTS}"])
    paths.collect_paths(filename=name, pathsname=name)
    results = paths.results_manager.get_named_results(name)
    assert len(results) == 1
    return results[0].csvpath.variables["counts"]


def test_count_bytes_is_zero_for_a_lone_csvpath():
    # the docs: individual CsvPath instances do not write out data, so 0
    path = CsvPath()
    path.parse(f"${PATH}[*][ push(\"counts\", count_bytes()) ]")
    lines = path.collect()
    counts = path.variables["counts"]
    # the header row plus 4 data rows, all collected, all 0
    assert len(lines) == 5
    assert counts == [0, 0, 0, 0, 0]


def test_count_bytes_starts_at_zero_in_a_named_paths_run():
    # on the first line nothing has been written to data.csv yet
    counts = _group_counts()
    assert len(counts) == 5
    assert counts[0] == 0


def test_count_bytes_never_goes_down():
    # bytes written only accumulate, so the count can lag but not shrink
    counts = _group_counts()
    assert all(isinstance(c, int) for c in counts)
    assert all(c >= 0 for c in counts)
    assert counts == sorted(counts)
