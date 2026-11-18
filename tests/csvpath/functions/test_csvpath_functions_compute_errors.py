"""Errors raised while a function computes its value or match (T1).

A ValueError or TypeError inside a function's _produce_value() or
_decide_match() used to be only logged: the value was a silent None, or,
for a match, the line matched. David, 2026-11-18: such an error is
recorded, raises in raise mode, and the line fails. If an error was
already recorded for the function on that line, e.g. by argument
validation, the second one is only logged, so one problem is not counted
twice.
"""

import os
import pytest
from csvpath import CsvPath
from csvpath.matching.util.exceptions import MatchException

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"

#
# each passes argument validation but fails while computing
#
SILENT_BEFORE = [
    ('gt("1,000", 9999)', "gt"),
    ('@r = mod("", 2)', "mod"),
    ('@r = format(3.14159, ":.2f")', "format"),
]


def _path(*, mode: str, csvpath: str) -> CsvPath:
    path = CsvPath()
    path.config.add_to_config("errors", "csvpath", mode)
    path.parse(csvpath)
    return path


@pytest.mark.parametrize("expression,name", SILENT_BEFORE)
def test_raise_mode_raises_a_match_exception(expression, name):
    path = _path(mode="raise", csvpath=f"${PATH}[1][ {expression} ]")
    with pytest.raises(MatchException) as e:
        path.collect()
    assert str(e.value).startswith(f"{name}: ")


@pytest.mark.parametrize("expression,name", SILENT_BEFORE)
def test_collect_mode_records_one_error_and_fails_the_line(expression, name):
    path = _path(mode="collect", csvpath=f"${PATH}[1][ {expression} ]")
    lines = path.collect()
    assert len(lines) == 0
    assert len(path.errors) == 1
    assert path.errors[0].message.startswith(f"{name}: ")


@pytest.mark.parametrize("expression,name", SILENT_BEFORE)
def test_one_error_per_line(expression, name):
    # the already-recorded mark is per line: each bad line gets its own error
    path = _path(mode="collect", csvpath=f"${PATH}[1-3][ {expression} ]")
    assert len(path.collect()) == 0
    assert len(path.errors) == 3


def test_mod_of_blank_value_is_none():
    path = _path(mode="collect", csvpath=f'${PATH}[1][ @r = mod("", 2) ]')
    path.fast_forward()
    assert path.variables["r"] is None


def test_an_argument_error_is_not_counted_twice():
    # Args rejects "five"; add() then fails computing. one error, not two.
    path = _path(mode="collect", csvpath=f'${PATH}[1][ @r = add("five", 1) ]')
    assert len(path.collect()) == 0
    assert len(path.errors) == 1
    assert "add requires" in path.errors[0].message


def test_an_argument_error_raises_once_in_raise_mode():
    path = _path(mode="raise", csvpath=f'${PATH}[1][ @r = add("five", 1) ]')
    with pytest.raises(MatchException) as e:
        path.collect()
    assert "add requires" in str(e.value)


@pytest.mark.parametrize(
    "expression", ['@r = mod(5, 2)', "gt(10000, 9999)", '@r = format(3.14159, ".2f")']
)
def test_good_input_is_unchanged(expression):
    path = _path(mode="raise", csvpath=f"${PATH}[1][ {expression} ]")
    assert len(path.collect()) == 1
    assert len(path.errors) == 0


def test_only_the_bad_lines_fail(tmp_path):
    # the mark is reset per line: a bad value fails its own line only
    f = tmp_path / "mixed.csv"
    f.write_text("n\n4\nx\n6\n,\n8\n")
    path = _path(mode="collect", csvpath=f"${f}[1*][ @r = mod(#n, 2) ]")
    lines = path.collect()
    assert [line[0] for line in lines] == ["4", "6", "8"]
    assert len(path.errors) == 2
