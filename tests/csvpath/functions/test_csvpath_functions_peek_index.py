"""peek() and peek_eq() etc. accept any valid Python index, negative included,
and treat an index out of range in either direction as missing.

Before the fix:
- peek_eq and its siblings checked abs(i) < len(stack), so -1 on a one-item
  stack and -2 on a two-item stack were "out of range".
- peek() checked only i < len(stack), so a negative index past the start,
  e.g. peek("s", -2) on a one-item stack or peek("s", -1) on an empty one,
  raised IndexError.
"""

import os

import pytest

from csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


def _value(body: str):
    path = CsvPath()
    path.parse(f"~ validation-mode: raise, no-print ~ ${PATH}[1][ {body} ]")
    path.fast_forward()
    return path.variables.get("r")


ONE = 'push.nocontrib("s", 3)'
TWO = 'push.nocontrib("s", 3) push.nocontrib("s", 5)'


@pytest.mark.parametrize(
    "stack,index,expected",
    [
        (ONE, -1, True),
        (TWO, -1, False),
        (TWO, -2, True),
        (ONE, -2, False),
        (TWO, -3, False),
        (ONE, 0, True),
        (ONE, 1, False),
    ],
)
def test_peek_eq_index(stack, index, expected):
    assert _value(f"{stack} @r = peek_eq(\"s\", {index}, 3)") is expected


@pytest.mark.parametrize(
    "stack,index,expected",
    [
        (ONE, -1, 3),
        (TWO, -1, 5),
        (TWO, -2, 3),
        (ONE, -2, None),
        (TWO, -3, None),
        (ONE, 0, 3),
        (ONE, 1, None),
    ],
)
def test_peek_index(stack, index, expected):
    assert _value(f"{stack} @r = peek(\"s\", {index})") == expected


def test_peek_on_an_empty_stack_is_none():
    #
    # -1, the top, used to raise IndexError on an empty stack
    #
    assert _value('@r = peek("empty", -1)') is None
