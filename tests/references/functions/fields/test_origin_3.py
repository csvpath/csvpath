import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.origin_3 import Origin3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = Origin3()
    assert f.name == "origin"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.FILES, Reference3.CSVPATHS)
    assert f.SOURCE == "manifest"
    assert f.KEY == {
        Reference3.FILES: "from",
        Reference3.CSVPATHS: "source_path",
    }


def test_no_arg_is_valid():
    Origin3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Origin3(arg="x").check_valid()
