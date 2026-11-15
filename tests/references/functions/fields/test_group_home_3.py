import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.group_home_3 import GroupHome3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = GroupHome3()
    assert f.name == "group_home"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.CSVPATHS,)
    assert f.SOURCE == "manifest"
    assert f.KEY == {Reference3.CSVPATHS: "named_paths_home"}
    assert f.POSITIONS == {Reference3.CSVPATHS: (Reference3.NAME_ONE,)}


def test_no_arg_is_valid():
    GroupHome3().check_valid()  # should not raise


def test_a_string_arg_is_a_filter():
    # compendium 6.40: an argument to a field accessor filters (refused one
    # until 2026-11-15; RC triage A6/H)
    GroupHome3(arg="x").check_valid()  # should not raise


def test_a_non_string_arg_raises():
    with pytest.raises(ReferenceException3):
        GroupHome3(arg=5).check_valid()
