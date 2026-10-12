"""Functions that report an error raise only when the validation mode says
to raise.

xsd(), jsonschema(), roll(), year()/month()/day(), and line() tested
csvpath.do_i_raise without calling it. A bound method is always true, so
they raised in every mode. Expression catches those exceptions and
re-raises only in raise mode, so run outcomes were already right, but in
no-raise mode the rest of the function's work after the error was
skipped: e.g. line() did not run its argument validation.

These tests call the functions directly, below Expression, so they see
whether the function itself raises.
"""

import contextlib
import io
import os

import pytest

from csvpath import CsvPath
from csvpath.matching.util.exceptions import ChildrenException, MatchException

TEST_CSV = os.path.join("tests", "csvpath", "test_resources", "test.csv")
XSD_DIR = os.path.join("tests", "csvpath", "examples", "csvpath_examples_xsd")
JSON_DIR = os.path.join("tests", "csvpath", "examples", "csvpath_examples_jsonschema")
NO_RAISE = "print, no-raise, fail"


def _parsed(*, file: str, scan: str, body: str, mode: str = NO_RAISE) -> CsvPath:
    path = CsvPath()
    with contextlib.redirect_stdout(io.StringIO()):
        path.parse(f"~ validation-mode: {mode} ~ ${file}{scan}[ {body} ]")
    return path


def _collected(*, file: str, scan: str, body: str, mode: str = NO_RAISE) -> CsvPath:
    path = _parsed(file=file, scan=scan, body=body, mode=mode)
    with contextlib.redirect_stdout(io.StringIO()):
        path.collect()
    return path


def _first_function(path: CsvPath):
    return path.matcher.expressions[0][0].children[0]


#
# check_valid(): parse-time errors
#


def test_do_i_raise_line_check_valid_no_raise() -> None:
    path = _collected(
        file=TEST_CSV, scan="[1-3]", body="line(string(#firstname), count())"
    )
    line = _first_function(path)
    assert line.name == "line"
    with contextlib.redirect_stdout(io.StringIO()):
        line.check_valid()


def test_do_i_raise_line_check_valid_raise_mode() -> None:
    path = CsvPath()
    with pytest.raises(ChildrenException, match="Incorrect types"):
        with contextlib.redirect_stdout(io.StringIO()):
            path.parse(
                f"~ validation-mode: print, raise ~ ${TEST_CSV}[1-3][ line(string(#firstname), count()) ]"
            )
            path.collect()


def test_do_i_raise_line_no_raise_also_validates_args() -> None:
    #
    # the rest of check_valid() now runs in no-raise mode, so the argument
    # validation reports the bad argument too
    #
    path = _collected(
        file=TEST_CSV, scan="[1-3]", body="line(string(#firstname), count())"
    )
    messages = [e.message for e in path.errors]
    assert any(m.startswith("Incorrect types in line definition") for m in messages)
    assert any("arg 2 is an unexpected type" in m for m in messages)
    assert path.is_valid is False


def test_do_i_raise_roll_check_valid_no_raise() -> None:
    path = _collected(file=TEST_CSV, scan="[1-3]", body='@r = roll(now(), 2, "fish")')
    roll = path.matcher.expressions[0][0].children[0].right
    assert roll.name == "roll"
    with contextlib.redirect_stdout(io.StringIO()):
        roll.check_valid()


def test_do_i_raise_roll_no_raise_run_continues() -> None:
    path = _collected(
        file=TEST_CSV,
        scan="[1-3]",
        body='@r = roll(now(), 2, "fish") push("seen", line_number())',
    )
    assert path.is_valid is False
    assert any(
        m.startswith("Units must be one of") for m in [e.message for e in path.errors]
    )
    assert path.variables["seen"] == [1, 2, 3]


#
# _produce_value(): run-time errors
#


def _document_function_after_run(*, file: str, body: str):
    path = _collected(file=file, scan="[0]", body=body)
    assert path.is_valid is False
    function = _first_function(path)
    function.reset()
    function.value = None
    return path, function


def test_do_i_raise_xsd_invalid_document_no_raise() -> None:
    xsd = os.path.join(XSD_DIR, "automobiles.xsd")
    path, function = _document_function_after_run(
        file=os.path.join(XSD_DIR, "automobiles_bad.xml"), body=f'xsd("{xsd}")'
    )
    assert function.name == "xsd"
    #
    # _produce_value() directly: after the run the csvpath is stopped, so
    # to_value() would answer with the frozen no-op value
    #
    with contextlib.redirect_stdout(io.StringIO()):
        function._produce_value()
    assert function.value is False


def test_do_i_raise_jsonschema_invalid_document_no_raise() -> None:
    schema = os.path.join(JSON_DIR, "automobiles.jsonschema")
    path, function = _document_function_after_run(
        file=os.path.join(JSON_DIR, "automobiles_bad.json"),
        body=f'jsonschema("{schema}")',
    )
    assert function.name == "jsonschema"
    #
    # _produce_value() directly: after the run the csvpath is stopped, so
    # to_value() would answer with the frozen no-op value
    #
    with contextlib.redirect_stdout(io.StringIO()):
        function._produce_value()
    assert function.value is False


@pytest.mark.parametrize(
    "file,body",
    [
        (
            os.path.join(XSD_DIR, "automobiles_bad.xml"),
            f'xsd("{os.path.join(XSD_DIR, "automobiles.xsd")}")',
        ),
        (
            os.path.join(JSON_DIR, "automobiles_bad.json"),
            f'jsonschema("{os.path.join(JSON_DIR, "automobiles.jsonschema")}")',
        ),
    ],
)
def test_do_i_raise_document_validation_raise_mode(file: str, body: str) -> None:
    with pytest.raises(MatchException):
        _collected(file=file, scan="[0]", body=body, mode="print, raise")
