import pytest

from csvpath.references.functions.selectors.from_3 import From3
from csvpath.references.functions.selectors.index_3 import Index3
from csvpath.references.functions.function_3 import Function3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = From3(arg=1)
    assert f.name == "from"
    assert f.ROLE == Function3.CONTEXT_SETTER
    assert f.DATATYPES == (Reference3.RESULTS,)


def test_int_arg_is_valid():
    From3(arg=-3).check_valid()  # should not raise


def test_nested_index_arg_is_valid():
    From3(arg=Index3(arg=-3)).check_valid()  # should not raise


def test_no_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        From3().check_valid()


def test_string_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        From3(arg="x").check_valid()
