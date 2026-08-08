import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.named_paths_identities_3 import (
    NamedPathsIdentities3,
)
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = NamedPathsIdentities3()
    assert f.name == "named_paths_identities"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.CSVPATHS,)
    assert f.SOURCE == "manifest"
    assert f.KEY == {Reference3.CSVPATHS: "named_paths_identities"}


def test_no_arg_is_valid():
    NamedPathsIdentities3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        NamedPathsIdentities3(arg="x").check_valid()
