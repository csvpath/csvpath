import pytest

from csvpath.references.functions.selectors.to_3 import To3
from csvpath.references.functions.selectors.index_3 import Index3
from csvpath.references.functions.function_3 import Function3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = To3(arg=1)
    assert f.name == "to"
    assert f.ROLE == Function3.CONTEXT_SETTER
    assert f.DATATYPES == (Reference3.RESULTS,)


def test_int_arg_is_valid():
    To3(arg=5).check_valid()  # should not raise


def test_nested_index_arg_is_valid():
    To3(arg=Index3(arg=5)).check_valid()  # should not raise


def test_no_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        To3().check_valid()


def test_string_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        To3(arg="x").check_valid()
