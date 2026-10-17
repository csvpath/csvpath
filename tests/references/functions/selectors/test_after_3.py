import pytest

from csvpath.references.functions.selectors.after_3 import After3
from csvpath.references.functions.selectors.date_3 import Date3
from csvpath.references.functions.selectors.index_3 import Index3
from csvpath.references.functions.filters.predicate_function_3 import (
    PredicateFunction3,
)
from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.reference_function_factory_3 import (
    ReferenceFunctionFactory,
)
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = After3(arg=1)
    assert f.name == "after"
    assert f.ROLE == Function3.CONTEXT_SETTER
    assert f.DATATYPES == (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)
    assert f.POSITIONS == {
        Reference3.FILES: (Reference3.NAME_THREE,),
        Reference3.CSVPATHS: (Reference3.NAME_ONE, Reference3.NAME_THREE),
        Reference3.RESULTS: (Reference3.NAME_ONE, Reference3.NAME_THREE),
    }


def test_is_also_a_predicate_function():
    # extends PredicateFunction3, added 2026-10-17 -- the ':count(
    # :above(10))' worked example (normative examples 489-491) needs
    # ':above()' to also work as a scalar predicate, not just a range
    # bound. See Count3's own ARG_TYPES.
    assert isinstance(After3(arg=1), PredicateFunction3)


def test_int_arg_is_valid():
    After3(arg=-3).check_valid()  # should not raise


def test_nested_index_arg_is_valid():
    After3(arg=Index3(arg=-3)).check_valid()  # should not raise


def test_str_arg_is_valid():
    After3(arg="2025-01-01").check_valid()  # should not raise


def test_nested_date_arg_is_valid():
    After3(arg=Date3(arg="2025-01-01")).check_valid()  # should not raise


def test_no_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        After3().check_valid()


def test_non_leaf_type_is_rejected():
    with pytest.raises(ReferenceException3):
        After3(arg=1.5).check_valid()


class TestMatches:
    # scalar-predicate mode, added 2026-10-17 -- used nested inside
    # :count() (e.g. ':count(:above(10))'); the range-bound mode
    # (:apply_range()/:apply_date_range(), untouched) is exercised
    # elsewhere, via ResultsReferenceFinder3's own range tests.
    def test_int_bound_matches_strictly_greater(self):
        f = After3(arg=10)
        assert f.matches(11) is True
        assert f.matches(10) is False
        assert f.matches(9) is False

    def test_nested_index_bound_unwraps_same_as_range_bound(self):
        f = After3(arg=Index3(arg=10))
        assert f.matches(11) is True
        assert f.matches(10) is False

    def test_str_bound_matches_lexicographically(self):
        f = After3(arg="2025-01-01")
        assert f.matches("2025-01-02") is True
        assert f.matches("2025-01-01") is False
        assert f.matches("2024-12-31") is False


class TestAliases:
    # compendium 6.28b -- "above"/"gt" are aliases of ":after()"; "lte"/
    # "gte" are aliases of the EXISTING ":to()'/':from()' classes, not
    # new classes of their own.
    @pytest.mark.parametrize("alias", ["above", "gt"])
    def test_alias_resolves_to_after3(self, alias):
        assert ReferenceFunctionFactory.get_registered_class(alias) is After3

    def test_lte_resolves_to_to3(self):
        from csvpath.references.functions.selectors.to_3 import To3

        assert ReferenceFunctionFactory.get_registered_class("lte") is To3

    def test_gte_resolves_to_from3(self):
        from csvpath.references.functions.selectors.from_3 import From3

        assert ReferenceFunctionFactory.get_registered_class("gte") is From3

    @pytest.mark.parametrize("alias", ["above", "gt", "after"])
    def test_built_instance_name_is_always_canonical(self, alias):
        from csvpath.references.reference_3 import FunctionCall3

        instance = ReferenceFunctionFactory.build(FunctionCall3(name=alias, arg=1))
        assert instance.name == "after"
