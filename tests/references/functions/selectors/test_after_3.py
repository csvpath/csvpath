import pytest

from csvpath.references.functions.selectors.after_3 import After3
from csvpath.references.functions.selectors.date_3 import Date3
from csvpath.references.functions.selectors.index_3 import Index3
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
