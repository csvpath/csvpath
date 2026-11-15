import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.named_paths_group_3 import NamedPathsGroup3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = NamedPathsGroup3()
    assert f.name == "named_paths_group"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.FILES,)
    assert f.SOURCE == "definition"
    assert f.KEY == {Reference3.FILES: "on_arrival.named_paths_group"}


def test_no_arg_is_valid():
    NamedPathsGroup3().check_valid()  # should not raise


def test_a_string_arg_is_a_filter():
    # compendium 6.40: an argument to a field accessor filters (refused one
    # until 2026-11-15; RC triage A6/H)
    NamedPathsGroup3(arg="x").check_valid()  # should not raise


def test_a_non_string_arg_raises():
    with pytest.raises(ReferenceException3):
        NamedPathsGroup3(arg=5).check_valid()
