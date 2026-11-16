"""Table tests for the peek comparators and for peek_size() and its alias size().

Argument order, from docs/func_gen/peek_<op>.md: (stack name, index, value).
The descriptions read "True if the stack value <op> the provided argument",
so the stack value is the left-hand side:

    peek_lt("s", 1, 6)  is  s[1] < 6

Every case runs on line 1 of test.csv only, after pushing 3 and then 5, so the
stack "s" is [3, 5].

What the docs leave unstated, and how it is handled here:

- Empty stack. docs/functions/pop.md:19 says peek() of an index that does not
  exist returns None. The comparators treat a missing value the same way for
  equality: peek_eq(empty, 0, none()) is True and peek_neq(empty, 0, none())
  is False. The ordering comparators are False because there is nothing to
  compare. These are pinned as current behavior.
- peek_neq() of a missing value against a real value is False today, which
  does not fit "a missing value is None". It is left out and reported.
- A None on top of the stack compared with an ordering comparator gives a
  value of None and no error. It is left out and reported.
- Negative indexes other than -1 are left out and reported, because
  peek_eq("s", -2, 3) is False although s[-2] is 3.
- size() used as a bare match component is left out and reported. It raises
  "'bool' object is not callable" on the second line.
"""

import os

import pytest

from csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"

COLLECT = "~ validation-mode: collect, no-raise, no-print ~"

# the stack used by most tests is [3, 5]
PUSH_3_5 = 'push("s", 3) push("s", 5)'


def _run(*, expression: str, setup: str = PUSH_3_5, mode: str = ""):
    """Runs setup, then the expression, on line 1. Returns the CsvPath and its lines."""
    path = CsvPath()
    path.parse(f"{mode} ${PATH}[1][ {setup} {expression} ]")
    lines = path.collect()
    return path, lines


def _value(*, expression: str, setup: str = PUSH_3_5):
    path, _ = _run(expression=f"@result = {expression}", setup=setup)
    assert "result" in path.variables
    return path.variables["result"]


# (function, index, value, expected), all against the stack [3, 5]
COMPARATOR_TABLE = [
    # peek_eq: stack value == value
    ("peek_eq", 0, 3, True),
    ("peek_eq", 1, 5, True),
    ("peek_eq", 1, 3, False),
    ("peek_eq", -1, 5, True),
    # peek_neq: stack value != value
    ("peek_neq", 1, 5, False),
    ("peek_neq", 1, 4, True),
    ("peek_neq", 0, 5, True),
    # peek_lt: stack value < value
    ("peek_lt", 1, 6, True),
    ("peek_lt", 1, 5, False),
    ("peek_lt", 1, 4, False),
    # peek_lte: stack value <= value
    ("peek_lte", 1, 6, True),
    ("peek_lte", 1, 5, True),
    ("peek_lte", 1, 4, False),
    # peek_gt: stack value > value
    ("peek_gt", 1, 4, True),
    ("peek_gt", 1, 5, False),
    ("peek_gt", 1, 6, False),
    # peek_gte: stack value >= value
    ("peek_gte", 1, 4, True),
    ("peek_gte", 1, 5, True),
    ("peek_gte", 1, 6, False),
]


@pytest.mark.parametrize("function,index,value,expected", COMPARATOR_TABLE)
def test_comparator_value(function, index, value, expected):
    expression = f'{function}("s", {index}, {value})'
    assert _value(expression=expression) is expected


@pytest.mark.parametrize("function,index,value,expected", COMPARATOR_TABLE)
def test_comparator_match(function, index, value, expected):
    # the comparators decide the match from their value, so a bare
    # comparator must match or fail the line the same way
    path, lines = _run(expression=f'{function}("s", {index}, {value})')
    assert (len(lines) == 1) is expected


@pytest.mark.parametrize(
    "function", ["peek_eq", "peek_neq", "peek_lt", "peek_lte", "peek_gt", "peek_gte"]
)
def test_comparator_does_not_change_the_stack(function):
    # peek, unlike pop, does not remove the value
    path, _ = _run(expression=f'@result = {function}("s", 1, 5)')
    assert path.variables["s"] == [3, 5]


@pytest.mark.parametrize(
    "function", ["peek_eq", "peek_neq", "peek_lt", "peek_lte", "peek_gt", "peek_gte"]
)
def test_comparator_creates_a_missing_stack(function):
    # each comparator doc says "The stack is created if not found"
    path, _ = _run(expression=f'@result = {function}("t", 0, 1)', setup="")
    assert path.variables["t"] == []


@pytest.mark.parametrize(
    "function,value,expected",
    [
        # pinned: a missing value is treated as None for equality
        ("peek_eq", "none()", True),
        ("peek_neq", "none()", False),
        # pinned: no value means no equality and no ordering
        ("peek_eq", 1, False),
        ("peek_lt", 1, False),
        ("peek_lte", 1, False),
        ("peek_gt", 1, False),
        ("peek_gte", 1, False),
    ],
)
def test_comparator_on_an_empty_stack(function, value, expected):
    # the docs do not cover an empty stack. These pin the current behavior;
    # see the module docstring.
    expression = f'{function}("t", 0, {value})'
    assert _value(expression=expression, setup="") is expected


def test_comparator_index_past_the_top():
    # index 2 does not exist in [3, 5], so it behaves like an empty stack
    assert _value(expression='peek_eq("s", 2, none())') is True
    assert _value(expression='peek_eq("s", 2, 5)') is False


@pytest.mark.parametrize(
    "function,value,expected",
    [
        ("peek_eq", "none()", True),
        ("peek_eq", 1, False),
        ("peek_neq", 1, True),
        ("peek_neq", "none()", False),
    ],
)
def test_equality_with_a_none_on_top(function, value, expected):
    # a pushed None is a real stack value, so equality compares it to the
    # provided value as usual
    setup = 'push("n", none())'
    path, _ = _run(expression=f'@result = {function}("n", 0, {value})', setup=setup)
    assert path.variables["n"] == [None]
    assert path.variables["result"] is expected


# ---------------------------------------------------------------------------
# peek_size() and size()
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("function", ["peek_size", "size"])
@pytest.mark.parametrize(
    "setup,expected",
    [
        ("", 0),
        ('push("s", 3)', 1),
        (PUSH_3_5, 2),
        ('push("s", none())', 1),
    ],
)
def test_size_by_stack_name(function, setup, expected):
    # size() is documented as the same function as peek_size()
    assert _value(expression=f'{function}("s")', setup=setup) == expected


@pytest.mark.parametrize("function", ["peek_size", "size"])
def test_size_creates_a_missing_stack(function):
    # "Unless the notnone qualifier is present, the stack is created if not found"
    path, _ = _run(expression=f'@result = {function}("nope")', setup="")
    assert path.variables["nope"] == []
    assert path.variables["result"] == 0


@pytest.mark.parametrize("function", ["peek_size", "size"])
def test_size_does_not_change_the_stack(function):
    path, _ = _run(expression=f'@result = {function}("s")')
    assert path.variables["s"] == [3, 5]
    assert path.variables["result"] == 2


@pytest.mark.parametrize("function", ["peek_size", "size"])
def test_size_rejects_a_non_stack_value(function):
    # the data signatures allow a stack name (str) or a stack (list, tuple
    # or None). An int is neither.
    path, lines = _run(
        expression=f"@result = {function}(@z)", setup="@z = 1", mode=COLLECT
    )
    assert lines == []
    assert path.variables.get("result") is None
    assert any(f"{function} requires a string" in e.message for e in path.errors)
