import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.named_file_home_3 import NamedFileHome3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = NamedFileHome3()
    assert f.name == "named_file_home"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.FILES,)
    assert f.SOURCE == "computed"
    assert f.KEY == {}


def test_no_arg_is_valid():
    NamedFileHome3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        NamedFileHome3(arg="x").check_valid()
