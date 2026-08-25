import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.group_file_3 import GroupFile3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = GroupFile3()
    assert f.name == "group_file"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.CSVPATHS,)
    assert f.SOURCE == "manifest"
    assert f.KEY == {Reference3.CSVPATHS: "group_file_path"}


def test_no_arg_is_valid():
    GroupFile3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        GroupFile3(arg="x").check_valid()
