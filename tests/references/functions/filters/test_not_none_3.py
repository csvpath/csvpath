import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.filters.not_none_3 import NotNone3
from csvpath.references.functions.filters.predicate_function_3 import (
    PredicateFunction3,
)
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = NotNone3()
    assert f.name == "not_none"
    assert f.ROLE == Function3.VALUE
    assert isinstance(f, PredicateFunction3)


def test_no_arg_is_valid():
    NotNone3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        NotNone3(arg="x").check_valid()


def test_matches_anything_but_none():
    assert NotNone3().matches(None) is False
    assert NotNone3().matches("") is True
    assert NotNone3().matches(0) is True
    assert NotNone3().matches(False) is True
