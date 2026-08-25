import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.file_path_3 import FilePath3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = FilePath3()
    assert f.name == "file_path"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.FILES,)
    assert f.SOURCE == "manifest"
    assert f.KEY == {Reference3.FILES: "file"}


def test_no_arg_is_valid():
    FilePath3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        FilePath3(arg="x").check_valid()
