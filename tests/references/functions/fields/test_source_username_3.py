import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.source_username_3 import SourceUsername3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = SourceUsername3(arg="email")
    assert f.name == "source_username"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.FILES,)
    assert f.SOURCE == "definition"
    assert f.KEY == {Reference3.FILES: "sources.{}.username"}


def test_string_arg_is_valid():
    SourceUsername3(arg="email").check_valid()  # should not raise


def test_missing_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        SourceUsername3().check_valid()


def test_non_string_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        SourceUsername3(arg=10).check_valid()
