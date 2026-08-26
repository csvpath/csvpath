import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.filters.not_empty_3 import NotEmpty3
from csvpath.references.functions.filters.predicate_function_3 import (
    PredicateFunction3,
)
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = NotEmpty3()
    assert f.name == "not_empty"
    assert f.ROLE == Function3.VALUE
    assert isinstance(f, PredicateFunction3)


def test_no_arg_is_valid():
    NotEmpty3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        NotEmpty3(arg="x").check_valid()


def test_matches_anything_but_the_empty_string():
    assert NotEmpty3().matches("") is False
    assert NotEmpty3().matches("x") is True
    assert NotEmpty3().matches(None) is True
