import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.script_on_complete_error_3 import (
    ScriptOnCompleteError3,
)
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = ScriptOnCompleteError3()
    assert f.name == "script_on_complete_error"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.CSVPATHS,)
    assert f.SOURCE == "definition"
    assert f.KEY == {Reference3.CSVPATHS: "scripts.on_complete_error"}


def test_no_arg_is_valid():
    ScriptOnCompleteError3().check_valid()  # should not raise


def test_a_string_arg_is_a_filter():
    # compendium 6.40: an argument to a field accessor filters (refused one
    # until 2026-11-15; RC triage A6/H)
    ScriptOnCompleteError3(arg="x").check_valid()  # should not raise


def test_a_non_string_arg_raises():
    with pytest.raises(ReferenceException3):
        ScriptOnCompleteError3(arg=5).check_valid()
