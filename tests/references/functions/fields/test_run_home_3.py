import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.run_home_3 import RunHome3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = RunHome3()
    assert f.name == "run_home"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.RESULTS,)
    assert f.SOURCE == "manifest"
    assert f.KEY == {Reference3.RESULTS: "run_home"}
    assert f.POSITIONS == {Reference3.RESULTS: (Reference3.NAME_ONE,)}


def test_no_arg_is_valid():
    RunHome3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        RunHome3(arg="x").check_valid()
