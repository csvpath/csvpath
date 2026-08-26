import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.source_address_3 import SourceAddress3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = SourceAddress3(arg="email")
    assert f.name == "source_address"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.FILES,)
    assert f.SOURCE == "definition"
    assert f.KEY == {Reference3.FILES: "sources.{}.address"}


def test_string_arg_is_valid():
    SourceAddress3(arg="email").check_valid()  # should not raise


def test_missing_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        SourceAddress3().check_valid()


def test_non_string_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        SourceAddress3(arg=10).check_valid()
