import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.type_3 import Type3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = Type3()
    assert f.name == "type"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.FILES,)
    assert f.SOURCE == "manifest"
    assert f.KEY == {Reference3.FILES: "type"}


def test_no_arg_is_valid():
    Type3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Type3(arg="x").check_valid()
