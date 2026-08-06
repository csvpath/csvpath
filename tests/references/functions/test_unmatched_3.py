import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.unmatched_3 import Unmatched3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = Unmatched3()
    assert f.name == "unmatched"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.RESULTS,)


def test_no_arg_is_valid():
    Unmatched3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Unmatched3(arg="x").check_valid()
