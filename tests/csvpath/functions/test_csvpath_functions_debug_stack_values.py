"""Value tests for do_when_stack() (alias when_do_stack()), vote_stack() and brief_stack_trace().

The existing tests for these functions mostly print. These assert on what
each one produces.

What the docs say (docs/func_gen/<name>.md):

- do_when_stack() returns a stack of bools, one per when/do (->) operator in
  the csvpath, in order. True means the operator fired on this line; False
  means it did not. when_do_stack() is registered as an alias for the same
  class.
- vote_stack() returns the votes of the match components on this line, as a
  stack. The votes come from the central record, so a component that has not
  voted yet shows None rather than True or False.
- brief_stack_trace() writes a shallow stack trace to the log or to print().
  With no argument it prints; with "log" it logs.

test.csv has a header row and then 8 data rows. Frog is the first name on data
rows 3 and 8; every data row except row 1 (David Kermit) has the last name Bat.
"""

import logging
import os

import pytest

from csvpath import CsvPath
from csvpath.util.printer import TestPrinter

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"

# whole-file scans see the header row as line 0, then the 8 data rows
FROG_LINES = [3, 8]
DATA_LINES = 9


def _variables(*, expression: str, lines: str = "1") -> dict:
    path = CsvPath()
    path.parse(f"${PATH}[{lines}][ {expression} ]")
    path.fast_forward()
    return path.variables


# ---------------------------------------------------------------------------
# do_when_stack() and when_do_stack()
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("function", ["do_when_stack", "when_do_stack"])
def test_do_when_stack_one_line(function):
    # three when/do operators: only the first fires
    variables = _variables(
        expression=f"""
            yes() -> @a = 1
            no() -> @b = 1
            no() -> @c = 1
            @result = {function}()
        """
    )
    assert variables["result"] == [True, False, False]
    # the stack agrees with which do sides actually ran
    assert variables["a"] == 1
    assert "b" not in variables
    assert "c" not in variables


@pytest.mark.parametrize("function", ["do_when_stack", "when_do_stack"])
def test_do_when_stack_order_follows_the_csvpath(function):
    # the stack is in the order the operators are written, not reversed
    variables = _variables(
        expression=f"""
            no() -> @a = 1
            no() -> @b = 1
            yes() -> @c = 1
            @result = {function}()
        """
    )
    assert variables["result"] == [False, False, True]


@pytest.mark.parametrize("function", ["do_when_stack", "when_do_stack"])
def test_do_when_stack_with_no_operators_is_empty(function):
    assert _variables(expression=f"@result = {function}()")["result"] == []


@pytest.mark.parametrize("function", ["do_when_stack", "when_do_stack"])
def test_do_when_stack_per_line(function):
    # the stack is recomputed for each line, so pushing it collects one
    # entry per line, True only where the condition held
    variables = _variables(
        expression=f"""
            #firstname == "Frog" -> @x = 1
            push("stacks", {function}())
        """,
        lines="*",
    )
    stacks = variables["stacks"]
    assert len(stacks) == DATA_LINES
    expected = [[i in FROG_LINES] for i in range(DATA_LINES)]
    assert stacks == expected


def test_when_do_stack_is_the_same_as_do_when_stack():
    # the alias must give exactly the same stack on the same line
    variables = _variables(
        expression="""
            yes() -> @a = 1
            no() -> @b = 1
            @one = do_when_stack()
            @two = when_do_stack()
        """
    )
    assert variables["one"] == variables["two"] == [True, False]


# ---------------------------------------------------------------------------
# vote_stack()
# ---------------------------------------------------------------------------


def test_vote_stack_records_earlier_votes():
    # one vote per match component. yes() and no() have already voted. The
    # last slot is vote_stack()'s own component, which counts as True. The
    # docs do not mention that slot; this pins it.
    variables = _variables(expression="yes() no() yes() @result = vote_stack()")
    assert variables["result"] == [True, False, True, True]


def test_vote_stack_alone():
    assert _variables(expression="@result = vote_stack()")["result"] == [True]


def test_vote_stack_shows_none_for_components_that_have_not_voted():
    # the docs: components that have not voted yet return None. The equality
    # comes after vote_stack(), so it has not voted when the stack is taken.
    variables = _variables(
        expression='push("votes", vote_stack()) #lastname == "Bat"', lines="*"
    )
    votes = variables["votes"]
    assert len(votes) == DATA_LINES
    assert all(v == [True, None] for v in votes)


def test_vote_stack_per_line_after_an_equality():
    # here the equality votes first, so each line's stack shows its result:
    # the header row and David Kermit are not Bats
    variables = _variables(
        expression='#lastname == "Bat" push("votes", vote_stack())', lines="*"
    )
    votes = variables["votes"]
    assert len(votes) == DATA_LINES
    expected = [[i not in (0, 1), True] for i in range(DATA_LINES)]
    assert votes == expected


# ---------------------------------------------------------------------------
# brief_stack_trace()
# ---------------------------------------------------------------------------


class _Collect(logging.Handler):
    """Collects log messages so a test can read what was logged."""

    def __init__(self):
        super().__init__(level=logging.DEBUG)
        self.messages = []

    def emit(self, record) -> None:
        self.messages.append(record.getMessage())


def _trace(*, argument: str) -> tuple[list[str], list[str]]:
    """Runs brief_stack_trace(argument) on line 1. Returns the printed and logged lines."""
    path = CsvPath()
    printer = TestPrinter()
    path.set_printers([printer])
    handler = _Collect()
    path.logger.addHandler(handler)
    level = path.logger.level
    path.logger.setLevel(logging.DEBUG)
    try:
        path.parse(f"${PATH}[1][ brief_stack_trace({argument}) ]")
        path.fast_forward()
    finally:
        path.logger.removeHandler(handler)
        path.logger.setLevel(level)
    return printer.lines, handler.messages


def _is_trace(*, lines: list[str]) -> bool:
    # a trace starts with a heading, then has File lines, one of which is
    # brief_stack_trace's own frame in debug.py
    return (
        len(lines) > 1
        and lines[0].startswith("Brief trace in thread:")
        and all(line.startswith("File ") for line in lines[1:])
        and any("debug.py" in line for line in lines[1:])
    )


@pytest.mark.parametrize("argument", ["", '"print"'])
def test_brief_stack_trace_prints(argument):
    # no argument, or "print", sends the trace to the printer, not the log
    printed, logged = _trace(argument=argument)
    assert _is_trace(lines=printed)
    assert not any("Brief trace" in m for m in logged)


def test_brief_stack_trace_logs():
    printed, logged = _trace(argument='"log"')
    assert printed == []
    trace = [m for m in logged if m.startswith("Brief trace") or m.startswith("File ")]
    assert _is_trace(lines=trace)
