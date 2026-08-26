import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.filters.none_3 import None3
from csvpath.references.functions.filters.predicate_function_3 import (
    PredicateFunction3,
)
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = None3()
    assert f.name == "none"
    assert f.ROLE == Function3.VALUE
    assert isinstance(f, PredicateFunction3)


def test_no_arg_is_valid():
    None3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        None3(arg="x").check_valid()


def test_matches_only_none():
    assert None3().matches(None) is True
    assert None3().matches("") is False
    assert None3().matches(False) is False
