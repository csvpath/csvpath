import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.valid_3 import Valid3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = Valid3()
    assert f.name == "valid"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.RESULTS,)
    assert f.SOURCE == "manifest"
    assert f.KEY == {
        Reference3.RESULTS: "all_valid",
        Reference3.RESULT: "valid",
    }


def test_no_arg_is_valid():
    Valid3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Valid3(arg="x").check_valid()
