import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.file_home_3 import FileHome3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = FileHome3()
    assert f.name == "file_home"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.FILES,)
    assert f.SOURCE == "manifest"
    assert f.KEY == {Reference3.FILES: "file_home"}
    assert f.POSITIONS == {Reference3.FILES: (Reference3.NAME_THREE,)}


def test_no_arg_is_valid():
    FileHome3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        FileHome3(arg="x").check_valid()
