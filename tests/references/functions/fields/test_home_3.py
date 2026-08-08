import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.home_3 import Home3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = Home3()
    assert f.name == "home"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.FILES, Reference3.CSVPATHS)
    assert f.SOURCE == "manifest"
    assert f.KEY == {
        Reference3.FILES: "file_home",
        Reference3.CSVPATHS: "named_paths_home",
    }


def test_no_arg_is_valid():
    Home3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Home3(arg="x").check_valid()
