import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.instance_index_3 import InstanceIndex3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = InstanceIndex3()
    assert f.name == "instance_index"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.RESULTS,)
    assert f.SOURCE == "manifest"
    assert f.KEY == {Reference3.RESULT: "instance_index"}


def test_no_arg_is_valid():
    InstanceIndex3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        InstanceIndex3(arg="x").check_valid()
