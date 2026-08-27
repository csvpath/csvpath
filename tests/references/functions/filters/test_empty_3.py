import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.filters.empty_3 import Empty3
from csvpath.references.functions.filters.predicate_function_3 import (
    PredicateFunction3,
)
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = Empty3()
    assert f.name == "empty"
    assert f.ROLE == Function3.VALUE
    assert isinstance(f, PredicateFunction3)


def test_no_arg_is_valid():
    Empty3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Empty3(arg="x").check_valid()


def test_matches_only_the_empty_string():
    assert Empty3().matches("") is True
    assert Empty3().matches("x") is False
    assert Empty3().matches(None) is False
