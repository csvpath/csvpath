import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.named_file_size_3 import NamedFileSize3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = NamedFileSize3()
    assert f.name == "named_file_size"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.RESULTS,)
    assert f.SOURCE == "manifest"
    assert f.KEY == {Reference3.RESULTS: "named_file_size"}


def test_no_arg_is_valid():
    NamedFileSize3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        NamedFileSize3(arg="x").check_valid()
