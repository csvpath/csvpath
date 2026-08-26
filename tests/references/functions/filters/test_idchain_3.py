import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.filters.idchain_3 import Idchain3
from csvpath.references.functions.filters.not_none_3 import NotNone3
from csvpath.references.functions.filters.predicate_function_3 import (
    PredicateFunction3,
)
from csvpath.references.reference_3 import Reference3, Regex3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = Idchain3(arg="add[0]string[2]")
    assert f.name == "idchain"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.RESULTS,)
    assert f.ARG_TYPES == (str, Regex3, PredicateFunction3)


def test_required_arg_present_and_correct_type_passes():
    Idchain3(arg="add[0]string[2]").check_valid()  # should not raise


def test_missing_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Idchain3().check_valid()


def test_wrong_arg_type_is_rejected():
    with pytest.raises(ReferenceException3):
        Idchain3(arg=5).check_valid()


def test_regex_arg_passes_check_valid():
    Idchain3(arg=Regex3(pattern="add\\[0\\]")).check_valid()  # should not raise


def test_invalid_regex_raises_at_construction():
    with pytest.raises(ReferenceException3):
        Idchain3(arg=Regex3(pattern="add[0"))


class TestMatches:
    # matches() is what the finder actually calls -- str is an exact
    # match (the original behavior), Regex3 is a search() (not anchored
    # to the start or the whole string).
    def test_str_arg_exact_match(self):
        assert Idchain3(arg="add[0]string[2]").matches("add[0]string[2]") is True

    def test_str_arg_no_partial_match(self):
        assert Idchain3(arg="add[0]").matches("add[0]string[2]") is False

    def test_regex_arg_matches_anywhere_in_the_value(self):
        idchain = Idchain3(arg=Regex3(pattern="add\\[0\\]"))
        assert idchain.matches("prefix.add[0]string[2]") is True

    def test_regex_arg_no_match(self):
        idchain = Idchain3(arg=Regex3(pattern="add\\[9\\]"))
        assert idchain.matches("add[0]string[2]") is False

    def test_none_value_does_not_match_either_arg_type(self):
        assert Idchain3(arg="add[0]").matches(None) is False
        assert Idchain3(arg=Regex3(pattern="add")).matches(None) is False

    def test_predicate_function_arg_delegates_to_its_own_matches(self):
        # compendium 5.36/4.13's own settled example --
        # ":idchain(:not_none())" means "any idchain at all".
        idchain = Idchain3(arg=NotNone3())
        assert idchain.matches("add[0]string[2]") is True
        assert idchain.matches(None) is False
