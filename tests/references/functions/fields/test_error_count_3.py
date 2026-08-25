import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.error_count_3 import ErrorCount3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = ErrorCount3()
    assert f.name == "error_count"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.RESULTS,)
    assert f.SOURCE == "manifest"
    assert f.KEY == {Reference3.RESULTS: "error_count"}


def test_no_arg_is_valid():
    ErrorCount3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        ErrorCount3(arg="x").check_valid()
