import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.status_3 import Status3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = Status3()
    assert f.name == "status"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.RESULTS,)
    assert f.SOURCE == "manifest"
    assert f.KEY == {Reference3.RESULTS: "status"}


def test_no_arg_is_valid():
    Status3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Status3(arg="x").check_valid()
