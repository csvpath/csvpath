import pytest

from csvpath.references.functions.selectors.regex_3 import RegexSelector3
from csvpath.references.functions.function_3 import Function3
from csvpath.references.reference_3 import Reference3, Regex3
from csvpath.references.reference_exceptions_3 import ReferenceException3


def test_metadata():
    f = RegexSelector3(arg="acme_.*")
    assert f.name == "regex"
    assert f.ROLE == Function3.CONTEXT_SETTER
    assert f.DATATYPES == (Reference3.FILES, Reference3.CSVPATHS, Reference3.RESULTS)
    assert f.POSITIONS == {
        Reference3.FILES: (Reference3.ROOT_MAJOR,),
        Reference3.CSVPATHS: (Reference3.ROOT_MAJOR,),
        Reference3.RESULTS: (Reference3.ROOT_MAJOR,),
    }


def test_no_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        RegexSelector3().check_valid()


def test_str_arg_is_valid():
    RegexSelector3(arg="acme_.*").check_valid()  # should not raise


def test_regex3_arg_is_valid():
    RegexSelector3(arg=Regex3(pattern="acme_.*")).check_valid()  # should not raise


def test_non_str_non_regex_arg_is_rejected():
    with pytest.raises(ReferenceException3):
        RegexSelector3(arg=5).check_valid()


def test_invalid_regex_pattern_raises_at_check_valid_time():
    # fail fast at build time, same as Name3's own eager regex-syntax
    # check -- not later, deep inside name matching.
    with pytest.raises(ReferenceException3):
        RegexSelector3(arg="(unclosed").check_valid()


def test_invalid_regex3_pattern_raises_at_check_valid_time():
    with pytest.raises(ReferenceException3):
        RegexSelector3(arg=Regex3(pattern="(unclosed")).check_valid()


class TestPattern:
    # .pattern gives the raw pattern string uniformly, regardless of
    # which arg form was used.
    def test_pattern_from_a_plain_str_arg(self):
        assert RegexSelector3(arg="acme_.*").pattern == "acme_.*"

    def test_pattern_from_a_regex3_arg(self):
        assert RegexSelector3(arg=Regex3(pattern="acme_.*")).pattern == "acme_.*"
