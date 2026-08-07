import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.time_3 import Time3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = Time3()
    assert f.name == "time"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.FILES, Reference3.CSVPATHS)
    assert f.SOURCE == "manifest"
    assert f.KEY == {Reference3.FILES: "time", Reference3.CSVPATHS: "time"}


def test_no_arg_is_valid():
    Time3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Time3(arg="x").check_valid()
