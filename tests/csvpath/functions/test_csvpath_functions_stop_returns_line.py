"""stop() returns the line it stops on, wherever it sits in the csvpath
(#483). The line is decided by the components that ran before the stop
and the stop's own component. Components after the stop do not run, and
no later line is considered."""

import pytest

from csvpath import CsvPath

STOP_ON_2 = "line_number.nocontrib() == 2 -> {stop}()"


@pytest.fixture
def data(tmp_path) -> str:
    p = tmp_path / "four_lines.csv"
    p.write_text("a,b\n1,2\n3,4\n5,6\n", encoding="utf-8")
    return str(p)


def _collect(data: str, body: str, *, logic: str | None = None):
    md = f"~ logic-mode: {logic} ~\n" if logic else ""
    path = CsvPath()
    lines = path.collect(f"{md}${data}[*][ {body} ]")
    return path, [line[0] for line in lines]


@pytest.mark.parametrize("stop", ["stop", "stop_all", "fail_and_stop"])
@pytest.mark.parametrize(
    "body",
    [
        "yes() {s}",
        "yes() {s} yes()",
        "yes() {s} yes() yes()",
    ],
    ids=["last", "one-after", "two-after"],
)
def test_stop_returns_the_line_it_stops_on(data: str, stop: str, body: str) -> None:
    #
    # the result no longer depends on what follows the stop
    #
    path, matched = _collect(data, body.format(s=STOP_ON_2.format(stop=stop)))
    assert matched == ["a", "1", "3"]
    assert path.stopped is True


@pytest.mark.parametrize("stop", ["stop", "stop_all", "fail_and_stop"])
def test_stop_a_failing_component_after_it_does_not_run(data: str, stop: str) -> None:
    #
    # no() fails lines 0 and 1. on the stopping line it doesn't run, so the
    # line is decided by yes() and the stop
    #
    body = f"yes() {STOP_ON_2.format(stop=stop)} no()"
    path, matched = _collect(data, body)
    assert matched == ["3"]


@pytest.mark.parametrize("position", ["before", "after"])
def test_stop_conditional_form(data: str, position: str) -> None:
    stop = "stop(line_number() == 2)"
    body = f"yes() {stop}" if position == "before" else f"{stop} yes()"
    path, matched = _collect(data, body)
    assert matched == ["a", "1", "3"]


def test_stop_and_mode_line_that_already_failed_is_not_returned(data: str) -> None:
    #
    # the stop doesn't make a failed line match
    #
    for body in [
        f"no() {STOP_ON_2.format(stop='stop')}",
        f"no() {STOP_ON_2.format(stop='stop')} yes()",
    ]:
        path, matched = _collect(data, body)
        assert matched == []
        assert path.stopped is True


def test_stop_and_mode_earlier_condition_decides(data: str) -> None:
    body = f'not(#a == "3") {STOP_ON_2.format(stop="stop")} yes()'
    path, matched = _collect(data, body)
    assert matched == ["a", "1"]


def test_stop_or_mode_returns_the_line_if_something_matched(data: str) -> None:
    body = f"yes() {STOP_ON_2.format(stop='stop')} no()"
    path, matched = _collect(data, body, logic="OR")
    assert matched == ["a", "1", "3"]


def test_stop_or_mode_does_not_return_an_unmatched_line(data: str) -> None:
    body = f"no() {STOP_ON_2.format(stop='stop')} yes()"
    path, matched = _collect(data, body, logic="OR")
    #
    # yes() after the stop doesn't run, so line 2 has no matching component
    #
    assert matched == ["a", "1"]


def test_stop_or_mode_late_match_before_stop(data: str) -> None:
    #
    # a component just before the stop decides the line
    #
    body = f'no() #a == "3" {STOP_ON_2.format(stop="stop")} no()'
    path, matched = _collect(data, body, logic="OR")
    assert matched == ["3"]


def test_stop_components_after_it_do_not_run(data: str) -> None:
    body = f"counter.before(1) {STOP_ON_2.format(stop='stop')} counter.after(1)"
    path, matched = _collect(data, body)
    assert matched == ["a", "1", "3"]
    assert path.variables["before"] == 3
    #
    # after ran on lines 0 and 1, not on the stopping line
    #
    assert path.variables["after"] == 2


def test_stop_no_later_line_is_considered(data: str) -> None:
    body = f"counter.seen(1) {STOP_ON_2.format(stop='stop')} yes()"
    path, matched = _collect(data, body)
    assert path.variables["seen"] == 3
    assert path.line_monitor.physical_line_number == 2


def test_stop_on_the_first_line(data: str) -> None:
    body = "yes() line_number.nocontrib() == 0 -> stop() yes()"
    path, matched = _collect(data, body)
    assert matched == ["a"]


def test_stop_on_the_last_line(data: str) -> None:
    body = "yes() line_number.nocontrib() == 3 -> stop() yes()"
    path, matched = _collect(data, body)
    assert matched == ["a", "1", "3", "5"]


def test_already_stopped_csvpath_does_not_match_a_line(data: str) -> None:
    #
    # a csvpath stopped before a line's first component doesn't match it,
    # even in AND mode where an empty vote would otherwise be a match. the
    # run loops never hand such a line over, but the matcher doesn't rely
    # on that.
    #
    path, matched = _collect(data, "yes()")
    assert matched == ["a", "1", "3", "5"]
    path.stopped = True
    assert path.matcher.matches() is False
