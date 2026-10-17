import pytest

from csvpath.references.functions.filters.count_3 import Count3
from csvpath.references.functions.filters.predicate_function_3 import (
    PredicateFunction3,
)
from csvpath.references.functions.selectors.after_3 import After3
from csvpath.references.functions.function_3 import Function3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = Count3(arg=After3(arg=10))
    assert f.name == "count"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.RESULTS,)
    assert f.ARG_TYPES == (PredicateFunction3,)


def test_predicate_arg_is_valid():
    Count3(arg=After3(arg=10)).check_valid()  # should not raise


def test_no_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Count3().check_valid()


def test_non_predicate_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Count3(arg=10).check_valid()


class TestMatches:
    # the whole-list GATE mechanism, not a per-entry filter -- see
    # Count3's own class docstring and Errors3's "third exception"
    # comment. `data` is errors.json's own raw, UNFILTERED entry list.
    def test_count_above_bound_matches(self):
        f = Count3(arg=After3(arg=10))
        assert f.matches([{"source": "x"}] * 11) is True

    def test_count_at_bound_does_not_match(self):
        f = Count3(arg=After3(arg=10))
        assert f.matches([{"source": "x"}] * 10) is False

    def test_count_below_bound_does_not_match(self):
        f = Count3(arg=After3(arg=10))
        assert f.matches([{"source": "x"}] * 3) is False

    def test_missing_file_counts_as_zero(self):
        # errors.json never written -- same genuinely-optional
        # treatment every other well-known file gets, not an error.
        f = Count3(arg=After3(arg=10))
        assert f.matches(None) is False

    def test_empty_list_counts_as_zero(self):
        f = Count3(arg=After3(arg=0))
        # ':above(0)' with zero entries -- 0 is not > 0.
        assert f.matches([]) is False
