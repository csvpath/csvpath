import pytest

from csvpath.references.functions.first_3 import First3
from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.index_3 import Index3
from csvpath.references.functions.last_3 import Last3
from csvpath.references.functions.reference_function_factory_3 import (
    ReferenceFunctionFactory,
)
from csvpath.references.reference_3 import FunctionCall3
from csvpath.references.reference_exceptions_3 import ReferenceException3


class TestBuild:
    def test_rejects_none(self):
        with pytest.raises(ValueError):
            ReferenceFunctionFactory.build(None)

    def test_builds_first(self):
        f = ReferenceFunctionFactory.build(FunctionCall3(name="first"))
        assert isinstance(f, First3)

    def test_builds_last(self):
        f = ReferenceFunctionFactory.build(FunctionCall3(name="last"))
        assert isinstance(f, Last3)

    def test_builds_index(self):
        f = ReferenceFunctionFactory.build(FunctionCall3(name="index", arg=0))
        assert isinstance(f, Index3)
        assert f.arg == 0

    def test_unknown_function_raises(self):
        with pytest.raises(ReferenceException3):
            ReferenceFunctionFactory.build(FunctionCall3(name="not_a_real_function"))

    def test_built_function_is_check_valid_already(self):
        # last() takes no arg -- passing one should surface as a
        # ReferenceException3 from build(), not silently construct an
        # unvalidated instance.
        with pytest.raises(ReferenceException3):
            ReferenceFunctionFactory.build(FunctionCall3(name="last", arg="x"))

    def test_recursively_compiles_a_nested_function_call_arg(self):
        # neither first() nor last() takes a nested function arg, so a
        # temporary function is registered here to exercise build()'s
        # recursion for real: the outer function's arg must arrive as
        # an already-compiled, already-validated Function3 instance --
        # not the raw FunctionCall3 the transformer produced.
        class _Wraps3(Function3):
            NAME = "wraps_for_test"
            SUMMARY = "test-only: takes a nested function"
            ROLE = Function3.CONTEXT_SETTER
            DATATYPES = ()
            ARG_TYPES = (Function3,)
            ARG_REQUIRED = True

        ReferenceFunctionFactory.add_function(_Wraps3)
        try:
            call = FunctionCall3(name="wraps_for_test", arg=FunctionCall3(name="first"))
            built = ReferenceFunctionFactory.build(call)
            assert isinstance(built, _Wraps3)
            assert isinstance(built.arg, First3)
        finally:
            del ReferenceFunctionFactory._FUNCTIONS["wraps_for_test"]


class TestBuildChain:
    def test_single_pointer_is_fine(self):
        built = ReferenceFunctionFactory.build_chain([FunctionCall3(name="first")])
        assert len(built) == 1
        assert isinstance(built[0], First3)

    def test_two_pointers_in_the_same_chain_raises(self):
        with pytest.raises(ReferenceException3):
            ReferenceFunctionFactory.build_chain(
                [FunctionCall3(name="first"), FunctionCall3(name="last")]
            )

    def test_index_and_last_in_the_same_chain_also_raises(self):
        with pytest.raises(ReferenceException3):
            ReferenceFunctionFactory.build_chain(
                [FunctionCall3(name="index", arg=0), FunctionCall3(name="last")]
            )

    def test_empty_chain_is_fine(self):
        assert ReferenceFunctionFactory.build_chain([]) == []
