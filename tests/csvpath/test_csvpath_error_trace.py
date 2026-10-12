"""Error.trace and Error.expanded_message (#342).

Error.trace holds the stack trace of an unexpected exception. It is set
through ErrorManager.handle_error(trace=...), serialized to errors.json when
set, never printed, and not part of error equality. expanded_message, the
formatted line that is printed with the full error format, is now also
serialized.

jsonschema() used to print the trace of an unexpected exception (a missing
or unreadable schema) to the console; xsd() did not catch them. Both now put
the trace in the error.
"""

import contextlib
import io
import json
import os

import pytest

from csvpath import CsvPath
from csvpath.managers.errors.error import Error
from csvpath.matching.util.exceptions import MatchException
from csvpath.util.nos import Nos
from tests.csvpaths.builder import Builder

JSON_DIR = os.path.join("tests", "csvpath", "examples", "csvpath_examples_jsonschema")
XSD_DIR = os.path.join("tests", "csvpath", "examples", "csvpath_examples_xsd")
GOOD_JSON = os.path.join(JSON_DIR, "automobiles.json")
BAD_JSON = os.path.join(JSON_DIR, "automobiles_bad.json")
GOOD_XML = os.path.join(XSD_DIR, "automobiles.xml")
NO_RAISE = "print, no-raise, fail, collect"


def _run(*, file: str, body: str, mode: str = NO_RAISE):
    path = CsvPath()
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        path.parse(f"~ validation-mode: {mode} ~ ${file}[0][ {body} ]")
        path.collect()
    return path, out.getvalue()


#
# Error
#


def _error_manager():
    path, _ = _run(file=GOOD_JSON, body="yes()")
    return path.error_manager


def _error(msg: str = "m") -> Error:
    return Error(source="test", msg=msg, error_manager=_error_manager())


def test_error_trace_defaults_to_none_and_is_not_serialized() -> None:
    e = _error()
    assert e.trace is None
    assert e.expanded_message is None
    j = e.to_json()
    assert "trace" not in j
    assert "expanded_message" not in j


def test_error_trace_and_expanded_message_round_trip() -> None:
    e = _error()
    e.trace = "Traceback (most recent call last): ..."
    e.expanded_message = "time:file:0:::chain: m"
    j = e.to_json()
    assert j["trace"] == e.trace
    assert j["expanded_message"] == e.expanded_message
    f = _error(msg="other")
    f.from_json(j)
    assert f.trace == e.trace
    assert f.expanded_message == e.expanded_message


def test_error_trace_is_not_part_of_equality() -> None:
    em = _error_manager()
    e = Error(source="test", msg="m", error_manager=em)
    f = Error(source="test", msg="m", error_manager=em)
    f.trace = "a trace"
    f.expanded_message = "a decorated message"
    assert e.equals(f)


#
# ErrorManager.handle_error()
#


def test_handle_error_sets_trace() -> None:
    path, _ = _run(file=GOOD_JSON, body="yes()")
    with contextlib.redirect_stdout(io.StringIO()):
        path.error_manager.handle_error(source="test", msg="with trace", trace="T")
        path.error_manager.handle_error(source="test", msg="without trace")
    by_message = {e.message: e for e in path.errors}
    assert by_message["with trace"].trace == "T"
    assert by_message["without trace"].trace is None
    assert by_message["with trace"].expanded_message.endswith("with trace")


def test_handle_error_rejects_non_str_trace() -> None:
    path, _ = _run(file=GOOD_JSON, body="yes()")
    with pytest.raises(TypeError):
        path.error_manager.handle_error(source="test", msg="m", trace=1)


#
# jsonschema() and xsd()
#


@pytest.mark.parametrize(
    "label,file,body",
    [
        (
            "jsonschema missing schema",
            GOOD_JSON,
            'jsonschema("nope/missing.jsonschema")',
        ),
        (
            "jsonschema schema not json",
            GOOD_JSON,
            f'jsonschema("{os.path.join(XSD_DIR, "automobiles.xsd")}")',
        ),
        ("xsd missing xsd", GOOD_XML, 'xsd("nope/missing.xsd")'),
    ],
)
def test_unexpected_exception_trace_in_error_not_console(label, file, body) -> None:
    path, out = _run(file=file, body=body)
    assert "Traceback" not in out
    assert path.is_valid is False
    #
    # one error: the report from Expression for the same incident is dropped
    # as a duplicate, and the one with the trace is kept
    #
    assert path.errors_count == 1
    error = path.errors[0]
    assert error.trace is not None
    assert error.trace.startswith("Traceback")
    assert error.message in error.trace


@pytest.mark.parametrize(
    "file,body",
    [
        (GOOD_JSON, 'jsonschema("nope/missing.jsonschema")'),
        (GOOD_XML, 'xsd("nope/missing.xsd")'),
    ],
)
def test_unexpected_exception_raise_mode(file, body) -> None:
    with pytest.raises(MatchException):
        _run(file=file, body=body, mode="print, raise")


def test_validation_failure_has_no_trace() -> None:
    schema = os.path.join(JSON_DIR, "automobiles.jsonschema")
    path, _ = _run(file=BAD_JSON, body=f'jsonschema("{schema}")')
    assert path.is_valid is False
    assert path.errors_count == 1
    assert path.errors[0].trace is None


#
# errors.json
#


def _errors_json(
    *, name: str, file: str, csvpath: str, schema: str = None
) -> list[dict]:
    paths = Builder().build()
    paths.config.set(section="errors", name="csvpaths", value="print, no-raise, fail")
    paths.paths_manager.remove_named_paths(name)
    paths.paths_manager.add_named_paths(name=name, paths=[csvpath])
    paths.file_manager.add_named_file(name=name, path=file)
    if schema is not None:
        with open(schema, encoding="utf-8") as f:
            paths.paths_manager.asset_manager.store_asset_file(
                name=name, filename=os.path.basename(schema), contents=f.read()
            )
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            ref = paths.collect_paths(pathsname=name, filename=name)
        results = paths.results_manager.get_named_results(ref)
        path = Nos(results[0].instance_dir).join("errors.json")
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    finally:
        paths.paths_manager.remove_named_paths(name)
        paths.file_manager.remove_named_file(name)


def test_errors_json_has_trace_and_expanded_message() -> None:
    errors = _errors_json(
        name="error_trace_test",
        file=GOOD_JSON,
        csvpath='$[0][ jsonschema("missing.jsonschema") ]',
    )
    assert len(errors) == 1
    assert errors[0]["trace"].startswith("Traceback")
    assert errors[0]["expanded_message"].endswith(errors[0]["message"])


def test_errors_json_validation_failure_has_no_trace() -> None:
    errors = _errors_json(
        name="error_trace_test",
        file=BAD_JSON,
        csvpath='$[0][ jsonschema("automobiles.jsonschema") ]',
        schema=os.path.join(JSON_DIR, "automobiles.jsonschema"),
    )
    assert len(errors) >= 1
    for e in errors:
        assert "trace" not in e
        assert "expanded_message" in e
