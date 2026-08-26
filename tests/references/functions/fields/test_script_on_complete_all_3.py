import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.script_on_complete_all_3 import (
    ScriptOnCompleteAll3,
)
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = ScriptOnCompleteAll3()
    assert f.name == "script_on_complete_all"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.CSVPATHS,)
    assert f.SOURCE == "definition"
    assert f.KEY == {Reference3.CSVPATHS: "scripts.on_complete_all"}


def test_no_arg_is_valid():
    ScriptOnCompleteAll3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        ScriptOnCompleteAll3(arg="x").check_valid()
