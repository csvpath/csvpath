import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.time_completed_3 import TimeCompleted3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = TimeCompleted3()
    assert f.name == "time_completed"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.CSVPATHS, Reference3.RESULTS)
    assert f.SOURCE == "manifest"
    assert f.KEY == {
        Reference3.CSVPATHS: "time_completed",
        Reference3.RESULTS: "time_completed",
    }


def test_no_arg_is_valid():
    TimeCompleted3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        TimeCompleted3(arg="x").check_valid()
