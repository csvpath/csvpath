import pytest

from csvpath.references.functions.filters.does_not_have_value_3 import DoesNotHaveValue3
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
INT_FIELDS = ["instance_index", "named_file_size", "named_paths_count"]
BOOL_FIELDS = ["completed", "files_complete", "has_errors", "serial", "source_mode_preceding"]
STR_FIELDS = (
    "actual_data_file archive file_home file_name file_path group_file group_home "
    "host identity instance_home manifest_path mark method named_file_path origin "
    "origin_data_file preceding_instance_identity reference run_dir run_home username"
).split()


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


@pytest.mark.parametrize("name", STR_FIELDS)
def test_a_string_takes_a_str_or_has_value(name):
    # NRE ":has_value() and :does_not_have_value()": "Every field matches
    # exactly one of the two" (reviewer on #659: NRE 212 raised)
    _build(name, "x").check_valid()
    _build(name, HasValue3()).check_valid()
    _build(name, DoesNotHaveValue3()).check_valid()
    with pytest.raises(ReferenceException3):
        _build(name, True3()).check_valid()


@pytest.mark.parametrize(
    "stored, expected", [("3", 3), (3, 3), (None, None)]
)
def test_instance_index_reads_as_an_int(stored, expected):
    # the framework stores it as a string (Result.run_index; decision D23)
    cls = ReferenceFunctionFactory.get_registered_class("instance_index")
    assert cls.transform_value(stored) == expected


def test_an_instance_index_that_is_not_a_number_raises():
    cls = ReferenceFunctionFactory.get_registered_class("instance_index")
    with pytest.raises(ReferenceException3, match="not a whole number"):
        cls.transform_value("x")
