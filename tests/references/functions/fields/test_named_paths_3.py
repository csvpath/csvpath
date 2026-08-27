import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.named_paths_3 import NamedPaths3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = NamedPaths3()
    assert f.name == "named_paths"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.CSVPATHS,)
    assert f.SOURCE == "manifest"
    assert f.KEY == {Reference3.CSVPATHS: "named_paths"}


def test_no_arg_is_valid():
    NamedPaths3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        NamedPaths3(arg="x").check_valid()
