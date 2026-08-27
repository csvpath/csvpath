import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.filters.false_3 import False3
from csvpath.references.functions.filters.predicate_function_3 import (
    PredicateFunction3,
)
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = False3()
    assert f.name == "false"
    assert f.ROLE == Function3.VALUE
    assert isinstance(f, PredicateFunction3)


def test_no_arg_is_valid():
    False3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        False3(arg="x").check_valid()


def test_matches_only_python_false():
    assert False3().matches(False) is True
    assert False3().matches(True) is False
    assert False3().matches(None) is False
    assert False3().matches(0) is False
