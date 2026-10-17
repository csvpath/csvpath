import pytest

from csvpath.references.functions.function_3 import Function3
from csvpath.references.functions.filters.message_3 import Message3
from csvpath.references.functions.filters.not_none_3 import NotNone3
from csvpath.references.functions.filters.predicate_function_3 import (
    PredicateFunction3,
)
from csvpath.references.reference_3 import Reference3, Regex3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = Message3(arg="customer: 319")
    assert f.name == "message"
    assert f.ROLE == Function3.VALUE
    assert f.DATATYPES == (Reference3.RESULTS,)
    assert f.ARG_TYPES == (str, Regex3, PredicateFunction3)
    assert f.RESOLVES_AS == Reference3.METADATA_FIELD


def test_required_arg_present_and_correct_type_passes():
    Message3(arg="customer: 319").check_valid()  # should not raise


def test_missing_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        Message3().check_valid()


def test_wrong_arg_type_is_rejected():
    with pytest.raises(ReferenceException3):
        Message3(arg=5).check_valid()


def test_regex_arg_passes_check_valid():
    Message3(arg=Regex3(pattern="customer: 319")).check_valid()  # should not raise


def test_invalid_regex_raises_at_construction():
    with pytest.raises(ReferenceException3):
        Message3(arg=Regex3(pattern="customer: 319("))


class TestMatches:
    # matches() is what the finder actually calls -- str is an exact
    # match, Regex3 is a search() (not anchored to the start or the
    # whole string) -- identical semantics to Idchain3's own sibling
    # method, just over the "message" field instead of "source".
    def test_str_arg_exact_match(self):
        assert Message3(arg="customer: 319").matches("customer: 319") is True

    def test_str_arg_no_partial_match(self):
        assert Message3(arg="customer").matches("customer: 319") is False

    def test_regex_arg_matches_anywhere_in_the_value(self):
        message = Message3(arg=Regex3(pattern="customer: 319"))
        assert message.matches("error: customer: 319 not found") is True

    def test_regex_arg_no_match(self):
        message = Message3(arg=Regex3(pattern="customer: 999"))
        assert message.matches("customer: 319") is False

    def test_none_value_does_not_match_either_arg_type(self):
        assert Message3(arg="customer: 319").matches(None) is False
        assert Message3(arg=Regex3(pattern="customer")).matches(None) is False

    def test_predicate_function_arg_delegates_to_its_own_matches(self):
        # same settled shape as Idchain3's own ":idchain(:not_none())" --
        # ":message(:not_none())" means "any message at all".
        message = Message3(arg=NotNone3())
        assert message.matches("customer: 319") is True
        assert message.matches(None) is False
