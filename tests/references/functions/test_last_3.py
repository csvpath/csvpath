import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.last_3 import Last3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = Last3()
    assert f.name == "last"
    assert f.ROLE == Function3.POINTER
    assert f.DATATYPES == (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)


def test_no_arg_is_valid():
    Last3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Last3(arg="x").check_valid()
