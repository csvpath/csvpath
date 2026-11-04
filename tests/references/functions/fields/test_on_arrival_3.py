import pytest

from csvpath.references.functions.fields.on_arrival_3 import OnArrival3
from csvpath.references.functions.filters.has_value_3 import HasValue3
from csvpath.references.functions.filters.predicate_function_3 import (
    PredicateFunction3,
)
from csvpath.references.functions.function_3 import Function3
from csvpath.references.reference_3 import Reference3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = OnArrival3()
    assert f.name == "on_arrival"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.FILES,)
    assert f.SOURCE == "definition"
    assert f.KEY == {Reference3.FILES: "on_arrival"}
    assert f.ARG_TYPES == (PredicateFunction3,)


def test_no_arg_is_valid():
    OnArrival3().check_valid()  # should not raise


def test_plain_string_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        OnArrival3(arg="x").check_valid()


def test_predicate_arg_is_valid():
    # the generic predicate-argument filtering mechanism's own
    # motivating worked example -- ":on_arrival(:has_value())" nested
    # inside ":definition(...)" during '*' traversal. ARG_TYPES widened
    # 2026-10-17 (was: ()).
    OnArrival3(arg=HasValue3()).check_valid()  # should not raise
