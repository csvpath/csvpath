import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.selectors.name_3 import Name3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = Name3(arg="zero.csv")
    assert f.name == "name"
    assert f.ROLE == Function3.CONTEXT_SETTER
    assert f.DATATYPES == (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)


def test_str_arg_is_valid():
    Name3(arg="zero.csv").check_valid()  # should not raise


def test_missing_arg_raises():
    with pytest.raises(ReferenceException3):
        Name3().check_valid()


def test_non_str_arg_raises():
    with pytest.raises(ReferenceException3):
        Name3(arg=5).check_valid()
