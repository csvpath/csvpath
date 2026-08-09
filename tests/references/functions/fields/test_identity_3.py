import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.identity_3 import Identity3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = Identity3()
    assert f.name == "identity"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.RESULTS,)
    assert f.SOURCE == "manifest"
    assert f.KEY == {Reference3.RESULT: "instance_identity"}


def test_no_arg_is_valid():
    Identity3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Identity3(arg="x").check_valid()
