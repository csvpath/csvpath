import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.filters.does_not_have_value_3 import (
    DoesNotHaveValue3,
)
from csvpath.references.functions.filters.has_value_3 import HasValue3
from csvpath.references.functions.filters.predicate_function_3 import (
    PredicateFunction3,
)
from csvpath.references.functions.reference_function_factory_3 import (
    ReferenceFunctionFactory,
)
from csvpath.references.reference_exceptions_3 import ReferenceException3

#
# compendium 6.36 (David, 2026-11-03): a field has a value when it holds a
# primitive, including 0 and false, or a list or dict that is not empty.
# Every value matches exactly one of :has_value()/:does_not_have_value().
#
HAS_A_VALUE = ["x", " ", 0, 0.0, False, True, 7, [1], [None], {"a": 1}, b"x"]
HAS_NO_VALUE = ["", [], {}, None, b"", (), set()]


@pytest.mark.parametrize("cls", [HasValue3, DoesNotHaveValue3])
def test_metadata(cls):
    f = cls()
    assert f.ROLE == Function3.VALUE
    assert isinstance(f, PredicateFunction3)
    assert ReferenceFunctionFactory.get_registered_class(f.name) is cls


def test_names():
    assert HasValue3().name == "has_value"
    assert DoesNotHaveValue3().name == "does_not_have_value"


@pytest.mark.parametrize("cls", [HasValue3, DoesNotHaveValue3])
def test_no_arg_is_valid(cls):
    cls().check_valid()  # should not raise


@pytest.mark.parametrize("cls", [HasValue3, DoesNotHaveValue3])
def test_arg_is_rejected(cls):
    with pytest.raises(ReferenceException3):
        cls(arg="x").check_valid()


@pytest.mark.parametrize("value", HAS_A_VALUE)
def test_has_a_value(value):
    assert HasValue3().matches(value) is True
    assert DoesNotHaveValue3().matches(value) is False


@pytest.mark.parametrize("value", HAS_NO_VALUE)
def test_has_no_value(value):
    assert HasValue3().matches(value) is False
    assert DoesNotHaveValue3().matches(value) is True


@pytest.mark.parametrize("name", ["none", "not_none", "empty", "not_empty"])
def test_the_old_predicates_are_retired(name):
    # retired 2026-11-03, no aliases, the same way ':home()' was
    assert ReferenceFunctionFactory.get_registered_class(name) is None
