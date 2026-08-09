import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.named_file_name_3 import NamedFileName3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = NamedFileName3()
    assert f.name == "named_file_name"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.RESULTS, Reference3.FILES)
    assert f.SOURCE == "manifest"
    assert f.KEY == {
        Reference3.RESULTS: "named_file_name",
        Reference3.RESULT: "named_file_name",
    }


def test_no_arg_is_valid():
    NamedFileName3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        NamedFileName3(arg="x").check_valid()
