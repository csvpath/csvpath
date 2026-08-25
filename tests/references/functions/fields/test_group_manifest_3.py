import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.group_manifest_3 import GroupManifest3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = GroupManifest3()
    assert f.name == "group_manifest"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.CSVPATHS,)
    assert f.SOURCE == "manifest"
    assert f.KEY == {}
    assert f.LEDGER_KEY == {Reference3.CSVPATHS: "paths_manifest"}


def test_no_arg_is_valid():
    GroupManifest3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        GroupManifest3(arg="x").check_valid()
