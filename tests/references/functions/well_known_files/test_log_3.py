import pytest

from csvpath.references.functions.well_known_files.log_3 import Log3
from csvpath.references.functions.function_3 import Function3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = Log3()
    assert f.name == "log"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (
        Reference3.FILES,
        Reference3.CSVPATHS,
        Reference3.RESULTS,
    )
    assert f.ARG_TYPES == (int,)
    assert f.ARG_REQUIRED is False


def test_no_arg_is_valid():
    Log3().check_valid()  # should not raise


def test_int_arg_is_valid():
    Log3(arg=10).check_valid()  # should not raise


def test_string_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Log3(arg="10").check_valid()
