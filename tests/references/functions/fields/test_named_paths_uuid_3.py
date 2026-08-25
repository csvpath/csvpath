import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.named_paths_uuid_3 import NamedPathsUuid3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = NamedPathsUuid3()
    assert f.name == "named_paths_uuid"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.RESULTS,)
    assert f.SOURCE == "manifest"
    assert f.KEY == {
        Reference3.RESULTS: "named_paths_uuid",
        Reference3.RESULT: "named_paths_uuid",
    }


def test_no_arg_is_valid():
    NamedPathsUuid3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        NamedPathsUuid3(arg="x").check_valid()
