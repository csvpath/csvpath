import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.named_paths_name_3 import NamedPathsName3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = NamedPathsName3()
    assert f.name == "named_paths_name"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.CSVPATHS, Reference3.RESULTS)
    assert f.SOURCE == "manifest"
    assert f.KEY == {
        Reference3.CSVPATHS: "named_paths_name",
        Reference3.RESULTS: "named_paths_name",
    }


def test_no_arg_is_valid():
    NamedPathsName3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        NamedPathsName3(arg="x").check_valid()
