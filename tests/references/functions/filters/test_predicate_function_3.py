import pytest

from csvpath.references.functions.filters.predicate_function_3 import (
    PredicateFunction3,
)


def test_base_matches_is_not_implemented():
    class _Bare(PredicateFunction3):
        NAME = "bare"

    with pytest.raises(NotImplementedError):
        _Bare().matches("x")
