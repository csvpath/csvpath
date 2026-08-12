import pytest

from csvpath.references.functions.selectors.groups_3 import Groups3
from csvpath.references.functions.function_3 import Function3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = Groups3()
    assert f.name == "groups"
    assert f.ROLE == Function3.CONTEXT_SETTER
    assert f.DATATYPES == (Reference3.FILES, Reference3.RESULTS)


def test_no_arg_is_valid():
    Groups3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Groups3(arg="x").check_valid()
