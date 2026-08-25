import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.reference_field_3 import ReferenceField3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = ReferenceField3()
    assert f.name == "reference"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.FILES,)
    assert f.SOURCE == "manifest"
    assert f.KEY == {Reference3.FILES: "reference"}


def test_no_arg_is_valid():
    ReferenceField3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        ReferenceField3(arg="x").check_valid()
