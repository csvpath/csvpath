import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.meta_3 import Meta3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = Meta3()
    assert f.name == "meta"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.RESULTS,)


def test_no_arg_is_valid():
    Meta3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Meta3(arg="x").check_valid()
