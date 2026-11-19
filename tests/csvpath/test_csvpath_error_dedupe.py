"""ErrorManager drops a duplicate error whatever the error policy (#767).

An argument error is recorded where it is found, raised as a
MatchException, and recorded again by Expression.matches(). The duplicate
check used to compare only against collected errors, so with collect off
the error was printed twice under raise, print.
"""

import os
import pytest
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


def _run(*, policy: str, csvpath: str) -> tuple[CsvPath, list, bool]:
    path = CsvPath()
    path.config.add_to_config("errors", "csvpath", policy)
    printed = []
    path.print = lambda msg, *args, **kwargs: printed.append(msg)
    raised = False
    path.parse(csvpath)
    try:
        path.collect()
    except MatchException:
        raised = True
    return path, printed, raised


@pytest.mark.parametrize(
    "policy,raises",
    [
        ("print", False),
        ("raise, print", True),
        ("collect, print", False),
        ("raise, collect, print", True),
    ],
)
def test_an_argument_error_prints_once(policy, raises):
    _, printed, raised = _run(policy=policy, csvpath=f'${PATH}[1][ @r = add("five", 1) ]')
    assert raised is raises
    assert len(printed) == 1
    assert "add requires" in printed[0]


def test_collect_still_holds_one_error():
    path, _, _ = _run(
        policy="raise, collect, print", csvpath=f'${PATH}[1][ @r = add("five", 1) ]'
    )
    assert len(path.errors) == 1


def test_each_line_prints_its_own_error():
    # the record is per line: the same problem on three lines prints three times
    _, printed, _ = _run(policy="print", csvpath=f'${PATH}[1-3][ @r = add("five", 1) ]')
    assert len(printed) == 3


def test_different_errors_on_one_line_both_print():
    _, printed, _ = _run(
        policy="print",
        csvpath=f'${PATH}[1][ @r = add("five", 1) @s = subtract("six", 1) ]',
    )
    assert len(printed) == 2
