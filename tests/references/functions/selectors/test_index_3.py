import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.selectors.index_3 import Index3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = Index3(arg=0)
    assert f.name == "index"
    assert f.ROLE == Function3.POINTER
    assert f.DATATYPES == (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)


def test_zero_based_first_item_is_valid():
    Index3(arg=0).check_valid()  # should not raise


def test_positive_index_is_valid():
    Index3(arg=7).check_valid()  # should not raise


def test_missing_arg_raises():
    with pytest.raises(ReferenceException3):
        Index3().check_valid()


def test_non_int_arg_raises():
    with pytest.raises(ReferenceException3):
        Index3(arg="7").check_valid()
