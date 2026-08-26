import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.filters.true_3 import True3
from csvpath.references.functions.filters.predicate_function_3 import (
    PredicateFunction3,
)
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = True3()
    assert f.name == "true"
    assert f.ROLE == Function3.VALUE
    assert isinstance(f, PredicateFunction3)
    assert f.DATATYPES == (
        Reference3.FILES,
        Reference3.CSVPATHS,
        Reference3.RESULTS,
    )


def test_no_arg_is_valid():
    True3().check_valid()  # should not raise


def test_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        True3(arg="x").check_valid()


def test_matches_only_python_true():
    assert True3().matches(True) is True
    assert True3().matches(False) is False
    assert True3().matches(None) is False
    assert True3().matches(1) is False
