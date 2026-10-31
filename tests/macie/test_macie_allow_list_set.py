import pytest

from csvpath.macie.allow_list_set import AllowListSet
from csvpath.macie.macie_exceptions import MacieException


def test_macie_allow_empty_set_allows_nothing() -> None:
    assert not AllowListSet().allows(text="EMP-900001")


def test_macie_allow_regex_must_fully_match_the_occurrence() -> None:
    a = AllowListSet()
    a.add_regex(name="training", pattern=r"EMP-9\d{5}")
    assert a.allows(text="EMP-900001")
    assert not a.allows(text="EMP-900001X")
    assert not a.allows(text="xEMP-900001")
    assert not a.allows(text="EMP-123456")


def test_macie_allow_regex_is_case_sensitive_unless_it_says_so() -> None:
    a = AllowListSet()
    a.add_regex(name="r1", pattern=r"emp-9\d{5}")
    assert not a.allows(text="EMP-900001")
    a.add_regex(name="r2", pattern=r"(?i)emp-8\d{5}")
    assert a.allows(text="EMP-800001")


def test_macie_allow_words_exact_and_case_insensitive() -> None:
    a = AllowListSet()
    a.add_words(name="names", entries=["Akua Mansa", "", "  ", "425-555-0100"])
    assert a.allows(text="akua mansa")
    assert a.allows(text="AKUA MANSA")
    assert a.allows(text="425-555-0100")
    assert not a.allows(text="Akua  Mansa")
    assert not a.allows(text="Akua")


def test_macie_allow_several_lists_combine() -> None:
    a = AllowListSet()
    a.add_words(name="names", entries=["John Doe"])
    a.add_regex(name="training", pattern=r"EMP-9\d{5}")
    assert a.allows(text="john doe")
    assert a.allows(text="EMP-912345")
    assert a.names == ["names", "training"]


def test_macie_allow_bad_input() -> None:
    a = AllowListSet()
    with pytest.raises(ValueError):
        a.add_regex(name="", pattern="x")
    with pytest.raises(ValueError):
        a.add_words(name=None, entries=[])
    with pytest.raises(TypeError):
        a.add_words(name="w", entries="x")
    with pytest.raises(TypeError):
        a.add_words(name="w2", entries=["x", 1])
    with pytest.raises(MacieException):
        a.add_regex(name="r", pattern="(x")
    with pytest.raises(TypeError):
        a.allows(text=None)
    a.add_words(name="once", entries=["x"])
    with pytest.raises(ValueError, match="added twice"):
        a.add_regex(name="once", pattern="y")
