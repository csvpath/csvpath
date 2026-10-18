import pytest

from csvpath.references.functions.selectors.before_3 import Before3
from csvpath.references.functions.selectors.date_3 import Date3
from csvpath.references.functions.selectors.index_3 import Index3
from csvpath.references.functions.values.year_3 import Year3
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
    f = Before3(arg=1)
    assert f.name == "before"
    assert f.ROLE == Function3.CONTEXT_SETTER
    assert f.DATATYPES == (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)
    assert f.POSITIONS == {
        Reference3.FILES: (Reference3.NAME_THREE,),
        Reference3.CSVPATHS: (Reference3.NAME_ONE, Reference3.NAME_THREE),
        Reference3.RESULTS: (Reference3.NAME_ONE, Reference3.NAME_THREE),
    }


def test_is_also_a_predicate_function():
    # extends PredicateFunction3, added 2026-10-18 -- the
    # ":error_count(:below(1))" worked example (normative examples)
    # needs ":below()" to also work as a scalar predicate, not just a
    # range bound. See After3's own identical reasoning for ":above()".
    assert isinstance(Before3(arg=1), PredicateFunction3)


def test_int_arg_is_valid():
    Before3(arg=-3).check_valid()  # should not raise


def test_nested_index_arg_is_valid():
    Before3(arg=Index3(arg=-3)).check_valid()  # should not raise


def test_str_arg_is_valid():
    Before3(arg="2025-01-01").check_valid()  # should not raise


def test_nested_date_arg_is_valid():
    Before3(arg=Date3(arg="2025-01-01")).check_valid()  # should not raise


def test_no_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Before3().check_valid()


def test_non_leaf_type_is_rejected():
    with pytest.raises(ReferenceException3):
        Before3(arg=1.5).check_valid()


class TestMatches:
    # scalar-predicate mode, added 2026-10-18 -- used nested inside a
    # predicate-accepting field accessor (e.g. :error_count()); the
    # range-bound mode (_apply_range()/_apply_date_range(), untouched)
    # is exercised elsewhere.
    def test_int_bound_matches_strictly_less_than(self):
        f = Before3(arg=1)
        assert f.matches(0) is True
        assert f.matches(1) is False
        assert f.matches(2) is False

    def test_nested_index_bound_unwraps_same_as_range_bound(self):
        f = Before3(arg=Index3(arg=10))
        assert f.matches(9) is True
        assert f.matches(10) is False

    def test_time_window_function_bound_is_rejected_clearly(self):
        # nonsensical as a predicate -- comparing a plain count against
        # a date has no meaning. Same guard After3.matches() has.
        f = Before3(arg=Year3())
        with pytest.raises(ReferenceException3):
            f.matches(3)


class TestAliases:
    # compendium 6.28b -- "below"/"lt" are aliases of ":before()",
    # registered as additional ReferenceFunctionFactory dict keys
    # pointing at this same class (not separate classes).
    @pytest.mark.parametrize("alias", ["below", "lt"])
    def test_alias_resolves_to_before3(self, alias):
        assert ReferenceFunctionFactory.get_registered_class(alias) is Before3

    @pytest.mark.parametrize("alias", ["below", "lt", "before"])
    def test_built_instance_name_is_always_canonical(self, alias):
        # a built instance's own `.name` always reads back as "before"
        # regardless of which alias key reached the registry -- Function3
        # .name returns self.NAME, a class constant, not the parsed token.
        from csvpath.references.reference_3 import FunctionCall3

        instance = ReferenceFunctionFactory.build(FunctionCall3(name=alias, arg=1))
        assert instance.name == "before"
