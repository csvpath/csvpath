import pytest

from csvpath.references.functions.selectors.before_3 import Before3
from csvpath.references.functions.selectors.date_3 import Date3
from csvpath.references.functions.selectors.index_3 import Index3
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
