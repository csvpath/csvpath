"""stop_all() and skip_all() compared with stop() and skip() in a two-csvpath named-paths group.

What the docs say (docs/func_gen/<name>.md, docs/functions/stop.md):

- stop() halts its own csvpath. It "does not prevent any other csvpaths
  currently in progress as part of a named csvpaths set" from continuing.
- stop_all() halts its csvpath and "shuts down a whole named-paths group run
  when the run method is either breadth-first or the iterative programmatic
  next_paths() method". In next_paths() it "prevents subsequent csvpaths from
  running". The other serial methods are not in that list, so there it acts
  like stop().
- skip() jumps to the next line for its own csvpath. Later match components
  on that line are not evaluated.
- skip_all(): "In a named-paths group run, where the run method is
  breadth-first, skip_all() jumps to the next line without any following
  csvpaths seeing the line at all." In other run methods it acts like skip().

Each csvpath pushes line_number() for every line it fully evaluates. The csvpath
under test triggers stop/skip on line 3, before its push, so its own stack
shows where it stopped or skipped. test.csv has lines 0 to 8.

Each test registers the file and group under a unique name on the local backend.
"""

import os
import uuid

import pytest

from tests.csvpaths.builder import Builder

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"

ALL = [0, 1, 2, 3, 4, 5, 6, 7, 8]
UP_TO_2 = [0, 1, 2]
UP_TO_3 = [0, 1, 2, 3]
WITHOUT_3 = [0, 1, 2, 4, 5, 6, 7, 8]

BY_LINE = ["collect_by_line", "fast_forward_by_line", "next_by_line"]
SERIAL_NOT_NEXT = ["collect_paths", "fast_forward_paths"]


def _trigger(*, var: str, function: str) -> str:
    # the trigger comes before the push, so line 3 is not pushed by this csvpath
    return f'$[*][ line_number.nocontrib() == 3 -> {function}() push("{var}", line_number()) ]'


def _plain(*, var: str) -> str:
    return f'$[*][ push("{var}", line_number()) ]'


def _run(*, first: str, second: str, method: str) -> tuple[dict, int]:
    """Runs the group. Returns {identity: pushed line numbers} and the lines a next_ method yielded."""
    name = f"stop_skip_all_{uuid.uuid4().hex}"
    paths = Builder().build()
    paths.file_manager.add_named_file(name=name, path=PATH)
    paths.paths_manager.add_named_paths(
        name=name, paths=[f"~ id: one ~ {first}", f"~ id: two ~ {second}"]
    )
    run = getattr(paths, method)
    yielded = 0
    if method.startswith("next_"):
        for _ in run(filename=name, pathsname=name):
            yielded += 1
    else:
        run(filename=name, pathsname=name)
    results = paths.results_manager.get_named_results(name)
    seen = {}
    for r in results:
        seen[r.csvpath.identity] = r.csvpath.variables.get(r.csvpath.identity)
    return seen, yielded


# ---------------------------------------------------------------------------
# breadth-first runs
# ---------------------------------------------------------------------------


# (statement in which csvpath, function, one sees, two sees)
BY_LINE_TABLE = [
    # stop() only stops its own csvpath
    ("first", "stop", UP_TO_2, ALL),
    ("second", "stop", ALL, UP_TO_2),
    # stop_all() stops both. When the second csvpath calls it, the first
    # has already evaluated line 3.
    ("first", "stop_all", UP_TO_2, UP_TO_2),
    ("second", "stop_all", UP_TO_3, UP_TO_2),
    # skip() only skips the line for its own csvpath
    ("first", "skip", WITHOUT_3, ALL),
    ("second", "skip", ALL, WITHOUT_3),
    # skip_all() hides the line from the following csvpaths, not the earlier
    ("first", "skip_all", WITHOUT_3, WITHOUT_3),
    ("second", "skip_all", ALL, WITHOUT_3),
]


def _group(*, where: str, function: str) -> tuple[str, str]:
    if where == "first":
        return _trigger(var="one", function=function), _plain(var="two")
    return _plain(var="one"), _trigger(var="two", function=function)


@pytest.mark.parametrize("method", BY_LINE)
@pytest.mark.parametrize("where,function,one,two", BY_LINE_TABLE)
def test_by_line(method, where, function, one, two):
    first, second = _group(where=where, function=function)
    seen, _ = _run(first=first, second=second, method=method)
    assert seen == {"one": one, "two": two}


@pytest.mark.parametrize(
    "function,yielded",
    [
        # stop_all() on line 3 ends the run: lines 0-3 are yielded, the
        # last because the first csvpath returns the line it stopped on
        ("stop_all", 4),
        # stop() leaves the second csvpath running to the end
        ("stop", 9),
        # skip_all() means no csvpath yields line 3
        ("skip_all", 8),
        # skip() in the first csvpath still lets the second match line 3
        ("skip", 9),
    ],
)
def test_next_by_line_yields(function, yielded):
    first, second = _group(where="first", function=function)
    _, count = _run(first=first, second=second, method="next_by_line")
    assert count == yielded


# ---------------------------------------------------------------------------
# serial runs
# ---------------------------------------------------------------------------


def test_next_paths_stop_all_prevents_later_csvpaths():
    # the docs: in next_paths() stop_all() "prevents subsequent csvpaths
    # from running", so there is no result for the second csvpath
    first, second = _group(where="first", function="stop_all")
    seen, _ = _run(first=first, second=second, method="next_paths")
    assert seen == {"one": UP_TO_2}


def test_next_paths_stop_does_not_prevent_later_csvpaths():
    first, second = _group(where="first", function="stop")
    seen, _ = _run(first=first, second=second, method="next_paths")
    assert seen == {"one": UP_TO_2, "two": ALL}


def test_next_paths_stop_all_in_the_last_csvpath():
    # the earlier csvpath has already finished, so only the second stops
    first, second = _group(where="second", function="stop_all")
    seen, _ = _run(first=first, second=second, method="next_paths")
    assert seen == {"one": ALL, "two": UP_TO_2}


@pytest.mark.parametrize("method", SERIAL_NOT_NEXT)
def test_stop_all_acts_like_stop_in_other_serial_methods(method):
    # stop_all()'s group shutdown is documented only for breadth-first runs
    # and next_paths()
    first, second = _group(where="first", function="stop_all")
    seen, _ = _run(first=first, second=second, method=method)
    assert seen == {"one": UP_TO_2, "two": ALL}


@pytest.mark.parametrize("method", ["next_paths"] + SERIAL_NOT_NEXT)
def test_skip_all_acts_like_skip_in_serial_methods(method):
    # skip_all()'s cross-csvpath effect is documented only for breadth-first
    # runs, so in a serial run only its own csvpath skips the line
    first, second = _group(where="first", function="skip_all")
    seen, _ = _run(first=first, second=second, method=method)
    assert seen == {"one": WITHOUT_3, "two": ALL}
