import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.selectors.name_3 import Name3
from csvpath.references.reference_3 import Reference3, Regex3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = Name3(arg="zero.csv")
    assert f.name == "name"
    assert f.ROLE == Function3.CONTEXT_SETTER
    assert f.DATATYPES == (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)


def test_str_arg_is_valid():
    Name3(arg="zero.csv").check_valid()  # should not raise


def test_missing_arg_raises():
    with pytest.raises(ReferenceException3):
        Name3().check_valid()


def test_an_int_arg_is_valid():
    # decision D12 (2026-11-14): ':name(0)' is the statement identity "0"
    # as a name_three range bound; a path segment raises on it instead
    Name3(arg=5).check_valid()


def test_a_bool_arg_raises():
    # bool is an int subclass; ARG_TYPES alone lets it through
    with pytest.raises(ReferenceException3, match="boolean"):
        Name3(arg=True).check_valid()


def test_a_float_arg_raises():
    with pytest.raises(ReferenceException3):
        Name3(arg=5.5).check_valid()


def test_regex_arg_is_valid():
    # added 2026-08-27 -- see the "name_one path segment cannot be a
    # regex" bucket-list entry.
    Name3(arg=Regex3(pattern=r"^orders.*\.csv$")).check_valid()  # should not raise


def test_invalid_regex_arg_raises():
    with pytest.raises(ReferenceException3):
        Name3(arg=Regex3(pattern="(unclosed")).check_valid()
