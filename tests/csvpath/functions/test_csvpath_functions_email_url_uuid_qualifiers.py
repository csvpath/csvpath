"""notnone and distinct on email(), url() and uuid(), used standalone and inside line().

What the docs say:

- docs/functions/email.md: "unless the notnone qualifier is present, none() or
  None are accepted values". docs/func_gen/uuid.md says the same for uuid().
  docs/functions/types.md:46 says two delimiters with nothing between them is a
  none value.
- docs/qualifiers.md, notnone: "On a function, notnone disallows None-valued
  arguments ... declaring header values to be of a certain type and not None".
- docs/func_gen/email.md, url.md and uuid.md list notnone and distinct as
  match qualifiers. types.md describes distinct on line() as requiring the
  values to be unique within the dataset; on a type it is the same for that
  one value.

email_url_uuid.csv, scanned from line 1, so ids 1 to 4:

    1  a valid email, url and uuid
    2  all three blank (the None row)
    3  a duplicate of row 1
    4  different valid values

So for each function:

- plain: every row matches
- notnone: row 2 fails
- distinct: row 3 fails
- both: rows 2 and 3 fail

Every case runs in collect mode and asserts both the matched ids and the error
message. Raise mode is checked once per function and qualifier, standalone.

url() with a None variable or none() is not tested: it fails although the
docs say None is accepted. That is reported in the PR body rather than pinned.
"""

import os

import pytest

from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}email_url_uuid.csv"

COLLECT = "~ validation-mode: collect, no-raise, no-print ~"
RAISE = "~ validation-mode: raise, no-print ~"

FUNCTIONS = ["email", "url", "uuid"]

NOT_NONE_MESSAGE = "because it has the notnone qualifier"
DUPLICATE_MESSAGE = "Duplicate found on line 3"

# (qualifiers, ids expected to match, messages expected among the errors)
QUALIFIER_TABLE = [
    ("", ["1", "2", "3", "4"], []),
    (".notnone", ["1", "3", "4"], [NOT_NONE_MESSAGE]),
    (".distinct", ["1", "2", "4"], [DUPLICATE_MESSAGE]),
    (".notnone.distinct", ["1", "4"], [NOT_NONE_MESSAGE, DUPLICATE_MESSAGE]),
]


def _run(*, expression: str, mode: str = COLLECT) -> tuple[list[str], list[str]]:
    """Returns the matched ids and the error messages."""
    path = CsvPath()
    path.parse(f"{mode} ${PATH}[1*][ {expression} ]")
    lines = path.collect()
    return [line[0] for line in lines], [e.message for e in (path.errors or [])]


def _line_expression(*, function: str, qualifiers: str) -> str:
    # line() declares every header in order; only the function under test
    # carries the qualifiers
    types = {f: f"{f}(#{f})" for f in FUNCTIONS}
    types[function] = f"{function}{qualifiers}(#{function})"
    return f"line(string(#id), {types['email']}, {types['url']}, {types['uuid']})"


def _assert_messages(*, messages: list[str], expected: list[str]) -> None:
    if not expected:
        assert messages == []
    for want in expected:
        assert any(want in m for m in messages), f"{want!r} not in {messages}"


@pytest.mark.parametrize("function", FUNCTIONS)
@pytest.mark.parametrize("qualifiers,ids,expected", QUALIFIER_TABLE)
def test_standalone(function, qualifiers, ids, expected):
    matched, messages = _run(expression=f"{function}{qualifiers}(#{function})")
    assert matched == ids
    _assert_messages(messages=messages, expected=expected)


@pytest.mark.parametrize("function", FUNCTIONS)
@pytest.mark.parametrize("qualifiers,ids,expected", QUALIFIER_TABLE)
def test_inside_line(function, qualifiers, ids, expected):
    expression = _line_expression(function=function, qualifiers=qualifiers)
    matched, messages = _run(expression=expression)
    assert matched == ids
    _assert_messages(messages=messages, expected=expected)


@pytest.mark.parametrize("function", FUNCTIONS)
@pytest.mark.parametrize(
    "qualifier,message",
    [
        (".notnone", NOT_NONE_MESSAGE),
        (".distinct", DUPLICATE_MESSAGE),
    ],
)
def test_raise_mode(function, qualifier, message):
    path = CsvPath()
    path.parse(f"{RAISE} ${PATH}[1*][ {function}{qualifier}(#{function}) ]")
    with pytest.raises(MatchException, match=message):
        path.fast_forward()


@pytest.mark.parametrize("function", ["email", "uuid"])
@pytest.mark.parametrize("argument", ["none()", "@n"])
def test_none_value_is_accepted_without_notnone(function, argument):
    # email.md: "unless the notnone qualifier is present, none() or None are
    # accepted values"
    matched, messages = _run(expression=f"@n = none() {function}({argument})")
    assert matched == ["1", "2", "3", "4"]
    assert messages == []


@pytest.mark.parametrize("function", FUNCTIONS)
def test_none_variable_with_notnone_is_rejected(function):
    matched, messages = _run(expression=f"@n = none() {function}.notnone(@n)")
    assert matched == []
    _assert_messages(messages=messages, expected=[NOT_NONE_MESSAGE])
