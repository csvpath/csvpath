import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.run_uuid_3 import RunUuid3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = RunUuid3()
    assert f.name == "run_uuid"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.RESULTS,)
    assert f.SOURCE == "manifest"
    assert f.KEY == {
        Reference3.RESULTS: "run_uuid",
        Reference3.RESULT: "run_uuid",
    }


def test_no_arg_is_valid():
    RunUuid3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        RunUuid3(arg="x").check_valid()
