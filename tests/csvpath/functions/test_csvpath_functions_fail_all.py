"""fail_all() compared with fail() in a two-csvpath named-paths group.

What the docs say:

- docs/func_gen/fail.md: fail() "Indicates that a csvpath statement fails a
  data file." It fails its own csvpath.
- docs/func_gen/fail_all.md: fail_all() "Indicates that all csvpaths that are
  running as a group should be marked failed. I.e., the data file triggering
  the failure will have failed across the board, even if only one csvpath
  caught a problem."

Each test registers test.csv (9 lines, 0 to 8) and a two-csvpath group under
a unique name, on the local backend. The failing statement fires on line 3;
the other csvpath is just yes().

The breadth-first (_by_line) methods are tested with fail_all() in either
csvpath. For the serial (_paths) methods only next_paths() with fail_all() in
the first csvpath is tested. The other serial cases, and fail_all() on the
last line of a breadth-first run, leave the other csvpath valid. That is
reported in the PR body rather than pinned.
"""

import os
import uuid

import pytest

from tests.csvpaths.builder import Builder

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"

FAIL_ALL_ON_3 = "$[*][ line_number.nocontrib() == 3 -> fail_all() ]"
FAIL_ON_3 = "$[*][ line_number.nocontrib() == 3 -> fail() ]"
PASSES = "$[*][ yes() ]"

BY_LINE_METHODS = ["collect_by_line", "fast_forward_by_line", "next_by_line"]


def _run(*, first: str, second: str, method: str) -> tuple[list[bool], bool]:
    """Runs a two-csvpath group. Returns each result's is_valid and the group's."""
    name = f"fail_all_{uuid.uuid4().hex}"
    paths = Builder().build()
    paths.file_manager.add_named_file(name=name, path=PATH)
    paths.paths_manager.add_named_paths(
        name=name, paths=[f"~ id: one ~ {first}", f"~ id: two ~ {second}"]
    )
    run = getattr(paths, method)
    if method.startswith("next_"):
        # the next_ methods are generators; consume them to run
        for _ in run(filename=name, pathsname=name):
            pass
    else:
        run(filename=name, pathsname=name)
    results = paths.results_manager.get_named_results(name)
    assert [r.csvpath.identity for r in results] == ["one", "two"]
    return [r.is_valid for r in results], paths.results_manager.is_valid(name)


@pytest.mark.parametrize("method", BY_LINE_METHODS)
def test_no_failure_baseline(method):
    # without fail() or fail_all() both csvpaths are valid
    valid, group = _run(first=PASSES, second=PASSES, method=method)
    assert valid == [True, True]
    assert group is True


@pytest.mark.parametrize("method", BY_LINE_METHODS)
def test_fail_only_fails_its_own_csvpath(method):
    valid, group = _run(first=FAIL_ON_3, second=PASSES, method=method)
    assert valid == [False, True]
    assert group is False


@pytest.mark.parametrize("method", BY_LINE_METHODS)
def test_fail_in_the_second_csvpath_only_fails_the_second(method):
    valid, group = _run(first=PASSES, second=FAIL_ON_3, method=method)
    assert valid == [True, False]
    assert group is False


@pytest.mark.parametrize("method", BY_LINE_METHODS)
def test_fail_all_in_the_first_csvpath_fails_both(method):
    valid, group = _run(first=FAIL_ALL_ON_3, second=PASSES, method=method)
    assert valid == [False, False]
    assert group is False


@pytest.mark.parametrize("method", BY_LINE_METHODS)
def test_fail_all_in_the_second_csvpath_fails_both(method):
    # the first csvpath has already seen line 3 when the second fails all.
    # it is marked failed on the next line
    valid, group = _run(first=PASSES, second=FAIL_ALL_ON_3, method=method)
    assert valid == [False, False]
    assert group is False


def test_fail_all_in_a_serial_run_fails_the_later_csvpath():
    # next_paths() runs the csvpaths one after the other. fail_all() in the
    # first must still fail the second.
    valid, group = _run(first=FAIL_ALL_ON_3, second=PASSES, method="next_paths")
    assert valid == [False, False]
    assert group is False


def test_fail_in_a_serial_run_only_fails_its_own_csvpath():
    valid, group = _run(first=FAIL_ON_3, second=PASSES, method="next_paths")
    assert valid == [False, True]
