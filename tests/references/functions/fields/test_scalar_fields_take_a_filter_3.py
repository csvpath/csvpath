import pytest

from csvpath.references.functions.filters.has_value_3 import HasValue3
from csvpath.references.functions.filters.true_3 import True3
from csvpath.references.functions.reference_function_factory_3 import (
    ReferenceFunctionFactory,
)
from csvpath.references.reference_exceptions_3 import ReferenceException3

# compendium 6.40: "An argument to a field accessor filters too". These
# scalar fields refused an argument until 2026-11-15 (RC triage A6/H). Each
# takes the argument its value type's existing fields take: a string field
# a str (as :type()), a count an int or a predicate (as :error_count()), a
# flag a predicate (as :valid()). Time and collection fields are RC triage B5.
INT_FIELDS = ["instance_index", "named_file_size", "named_paths_count", "serial"]
BOOL_FIELDS = ["completed", "files_complete", "has_errors"]


def _build(name: str, arg):
    return ReferenceFunctionFactory.get_registered_class(name)(arg=arg)


@pytest.mark.parametrize("name", INT_FIELDS)
def test_a_count_takes_an_int_or_a_predicate(name):
    _build(name, 3).check_valid()
    _build(name, HasValue3()).check_valid()
    with pytest.raises(ReferenceException3):
        _build(name, "3").check_valid()


@pytest.mark.parametrize("name", BOOL_FIELDS)
def test_a_flag_takes_a_predicate(name):
    _build(name, True3()).check_valid()
    with pytest.raises(ReferenceException3):
        _build(name, "true").check_valid()
