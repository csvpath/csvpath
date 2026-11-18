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

The documented "runs behind" allows a lower count, never a higher one. Until
issue C1 was fixed the local count was higher: the spooler decided it was
remote before it knew its path, and counted the characters of str(line).
Counts during the run can be 0, because nothing is flushed yet; no test
pins an exact mid-run value.
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


DATA_CSV_BYTES = 45


def test_count_bytes_never_exceeds_the_bytes_in_data_csv():
    # it may run behind, but can never be ahead of what is on disk
    counts = _group_counts()
    assert max(counts) <= DATA_CSV_BYTES


def test_bytes_written_after_the_run_is_the_data_csv_size():
    name = f"count_bytes_{uuid.uuid4().hex}"
    paths = Builder().build()
    paths.file_manager.add_named_file(name=name, path=PATH)
    paths.paths_manager.add_named_paths(name=name, paths=[f"~ id: one ~ {PUSH_COUNTS}"])
    paths.collect_paths(filename=name, pathsname=name)
    result = paths.results_manager.get_named_results(name)[0]
    assert os.path.getsize(result.data_file_path) == DATA_CSV_BYTES
    assert result.csvpath.lines.bytes_written() == DATA_CSV_BYTES
