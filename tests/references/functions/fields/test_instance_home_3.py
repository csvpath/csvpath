import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.instance_home_3 import InstanceHome3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = InstanceHome3()
    assert f.name == "instance_home"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.RESULTS,)
    assert f.SOURCE == "manifest"
    assert f.KEY == {Reference3.RESULT: "instance_home"}
    assert f.POSITIONS == {Reference3.RESULTS: (Reference3.NAME_THREE,)}


def test_no_arg_is_valid():
    InstanceHome3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        InstanceHome3(arg="x").check_valid()
