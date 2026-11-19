"""or() and branch errors under each error policy (#760).

A True branch wins: the other branches' errors are dropped, with no raise,
in every policy (David, 2026-11-19, option a). When every branch fails,
the errors stand: they are recorded, printed, and in raise mode the run
stops. Before, a raising branch escaped or() during its argument check,
so raise mode stopped the run with nothing recorded, even when another
branch was True.
"""

import os
import pytest
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"
BAD = 'gt("1,000", 9999)'


def _run(*, policy: str, match: str) -> tuple[CsvPath, list, list, bool]:
    path = CsvPath()
    path.config.add_to_config("errors", "csvpath", policy)
    printed = []
    path.print = lambda msg, *args, **kwargs: printed.append(msg)
    raised = False
    lines = []
    path.parse(f"${PATH}[1][ {match} ]")
    try:
        lines = path.collect()
    except MatchException:
        raised = True
    return path, printed, lines, raised


POLICIES = ["raise", "collect", "print", "raise, collect, print", "collect, print"]


@pytest.mark.parametrize("policy", POLICIES)
@pytest.mark.parametrize("match", [f"or({BAD}, yes())", f"or(yes(), {BAD})"])
def test_a_true_branch_wins(policy, match):
    path, printed, lines, raised = _run(policy=policy, match=match)
    assert raised is False
    assert len(lines) == 1
    assert path.errors == []
    assert printed == []


@pytest.mark.parametrize("match", [f"or({BAD}, no())", f"or(no(), {BAD})"])
def test_all_branches_fail_raise_collect_print(match):
    path, printed, lines, raised = _run(policy="raise, collect, print", match=match)
    assert raised is True
    assert len(path.errors) == 1
    assert "could not convert" in path.errors[0].message
    assert len(printed) == 1


@pytest.mark.parametrize("match", [f"or({BAD}, no())", f"or(no(), {BAD})"])
def test_all_branches_fail_collect_print(match):
    path, printed, lines, raised = _run(policy="collect, print", match=match)
    assert raised is False
    assert lines == []
    assert len(path.errors) == 1
    assert len(printed) == 1


def test_all_branches_fail_raise_only_raises():
    # raise without collect: nothing is collected, but the run stops
    path, printed, lines, raised = _run(policy="raise", match=f"or({BAD}, no())")
    assert raised is True
    assert printed == []


def test_two_failing_branches_both_recorded():
    path, _, _, raised = _run(
        policy="collect", match=f'or({BAD}, gt("2,000", 9999))'
    )
    assert raised is False
    msgs = sorted(e.message for e in path.errors)
    assert len(msgs) == 2
    assert "'1,000'" in msgs[0]
    assert "'2,000'" in msgs[1]


@pytest.mark.parametrize("policy", POLICIES)
def test_no_errors_no_change(policy):
    path, printed, lines, raised = _run(policy=policy, match="or(gt(1, 2), yes())")
    assert raised is False
    assert len(lines) == 1
    assert path.errors == []


@pytest.mark.parametrize(
    "match",
    [
        # Expression records the raised error again; with a parent other
        # than or() as its source, that copy was not dropped
        f"not(or({BAD}, no()))",
        f"@x = or({BAD}, no())",
        f"or({BAD}, no())",
    ],
)
def test_all_branches_fail_records_once_under_a_parent(match):
    path, printed, _, raised = _run(policy="raise, collect, print", match=match)
    assert raised is True
    assert len(path.errors) == 1
    # or() is the source; the chain format itself is tested elsewhere
    assert path.errors[0].source.endswith("]")
    assert "or[" in path.errors[0].source
    assert len(printed) == 1


@pytest.mark.parametrize("policy,raises", [("raise, collect", True), ("collect", False)])
def test_nested_or_all_fail_stops_in_raise_mode(policy, raises):
    # the inner or() fails with an error and does not raise a second time;
    # the outer or() holds that error, so in raise mode the run stops
    path, _, lines, raised = _run(policy=policy, match=f"or(or({BAD}, no()), no())")
    assert raised is raises
    assert len(path.errors) == 1
    assert lines == []


def test_nested_or_true_inner_branch_wins():
    path, _, lines, raised = _run(
        policy="raise, collect", match=f"or(or({BAD}, yes()), no())"
    )
    assert raised is False
    assert len(lines) == 1
    assert path.errors == []
