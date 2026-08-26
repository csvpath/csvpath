import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.fields.destination_username_3 import (
    DestinationUsername3,
)
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = DestinationUsername3(arg="main")
    assert f.name == "destination_username"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.CSVPATHS,)
    assert f.SOURCE == "definition"
    assert f.KEY == {Reference3.CSVPATHS: "destinations.{}.username"}


def test_string_arg_is_valid():
    DestinationUsername3(arg="main").check_valid()  # should not raise


def test_missing_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        DestinationUsername3().check_valid()


def test_non_string_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        DestinationUsername3(arg=10).check_valid()
