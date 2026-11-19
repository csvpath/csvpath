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


PARITY = [
    f"or({BAD}, yes())",
    f"or({BAD}, no())",
    'or(add("five", 1), no())',
    'or(add("five", 1), yes())',
    f"or(not({BAD}), no())",
    f"or(or({BAD}, no()), no())",
    f"or(or({BAD}, yes()), no())",
    f"not(or({BAD}, no()))",
    "or(no(), no())",
    "or(gt(1, 2), yes())",
]


@pytest.mark.parametrize("match", PARITY)
def test_raise_mode_matches_print_mode(match):
    # David, 2026-11-19: in raise mode or() raises only if no branch is
    # True, and otherwise gives the same result as print mode
    _, p_printed, p_lines, p_raised = _run(policy="print", match=match)
    path, r_printed, r_lines, r_raised = _run(policy="raise, collect, print", match=match)
    assert p_raised is False
    if r_raised:
        # it raised: no or() branch was True, and print mode printed the
        # error. (in not(or(..)) the line still matches in print mode,
        # because not() turns or()'s False into True.)
        assert len(p_printed) >= 1
        assert len(path.errors) == 1
    else:
        assert len(r_lines) == len(p_lines)
        assert r_printed == p_printed


@pytest.mark.parametrize(
    "match", ['or(add("five", 1), no())', f"or(not({BAD}), no())"]
)
def test_an_erroring_branch_that_is_true_wins_in_raise_mode(match):
    # in print mode these branches are True despite the error, so they win
    path, printed, lines, raised = _run(policy="raise, collect, print", match=match)
    assert raised is False
    assert len(lines) == 1
    assert path.errors == []


def test_raise_is_resumed_after_or():
    # raising is paused only while or() runs its branches: an error after
    # it on the line still raises
    path, _, _, raised = _run(policy="raise, collect", match=f"or(yes(), {BAD}) {BAD}")
    assert raised is True
    assert path._raise_paused == 0


def test_resume_without_pause_is_an_error():
    path = CsvPath()
    with pytest.raises(RuntimeError):
        path.resume_raise()
