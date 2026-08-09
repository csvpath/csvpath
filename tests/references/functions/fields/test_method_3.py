import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.method_3 import Method3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = Method3()
    assert f.name == "method"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.RESULTS,)
    assert f.SOURCE == "manifest"
    assert f.KEY == {Reference3.RESULTS: "method"}


def test_no_arg_is_valid():
    Method3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Method3(arg="x").check_valid()
