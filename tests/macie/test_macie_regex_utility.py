import pytest

from csvpath.macie.regex_utility import RegexUtility as reut
from csvpath.macie.macie_exceptions import MacieException


@pytest.mark.parametrize(
    "pattern",
    [
        r"EMP-\d{6}",
        r"[a-zA-Z0-9_.+\-]+@acme\.com",
        r"^\(?800\)?[ -]?\d{3}[ -]?\d{4}$",
        r"(?:apple|orange)",
        r"(apple|orange)",
        r"a(?i:b)c",
        r"[]a]x",
        r"[^]a]x",
        r"[\]]x",
        r"a\(b\)",
        r"x(?=y)",
        r"x(?<!y)",
    ],
)
def test_macie_regex_without_inline_flags_is_unchanged(pattern: str) -> None:
    assert reut.to_python(pattern=pattern) == pattern


@pytest.mark.parametrize(
    "pattern, python",
    [
        (r"(?i)ab", r"(?i:ab)"),
        (r"ab(?i)cd", r"ab(?i:cd)"),
        (r"ab(?i)cd(?m)ef", r"ab(?i:cd(?m:ef))"),
        (r"a(?i)b|c", r"a(?i:b)|(?i:c)"),
        (r"a|b(?i)c|d", r"a|b(?i:c)|(?i:d)"),
        (r"(x(?i)y|z)w", r"(x(?i:y)|(?i:z))w"),
        (r"(?i)a(?-i)b", r"(?i:a(?-i:b))"),
        (r"[(?i)]x", r"[(?i)]x"),
        (r"\(?i\)x", r"\(?i\)x"),
    ],
)
def test_macie_regex_inline_flags_become_scoped(pattern: str, python: str) -> None:
    assert reut.to_python(pattern=pattern) == python


@pytest.mark.parametrize(
    "pattern, text, matches",
    [
        (r"ab(?i)cd", "abCD", True),
        (r"ab(?i)cd", "ABcd", False),
        (r"a(?i)b|c", "C", True),
        (r"a(?i)b|c", "A", False),
        (r"(x(?i)y|z)w", "Zw", True),
        (r"(x(?i)y|z)w", "xYW", False),
        (r"(?i)a(?-i)b", "Ab", True),
        (r"(?i)a(?-i)b", "AB", False),
    ],
)
def test_macie_regex_inline_flags_keep_pcre_scope(pattern, text, matches) -> None:
    assert bool(reut.compile(pattern=pattern).fullmatch(text)) is matches


def test_macie_regex_digits_are_ascii_only() -> None:
    #
    # Arabic-Indic digits match Python's \d but not PCRE's default \d
    #
    rx = reut.compile(pattern=r"EMP-\d{6}")
    assert rx.fullmatch("EMP-123456")
    assert not rx.fullmatch("EMP-١٢٣٤٥٦")


@pytest.mark.parametrize("pattern", [r"(ab", r"ab)", r"[ab", r"a(?P<n>b)", r"a(?#c)b"])
def test_macie_regex_malformed_or_unsupported(pattern: str) -> None:
    with pytest.raises(MacieException):
        reut.compile(pattern=pattern)


def test_macie_regex_python_compile_error_is_a_macie_exception() -> None:
    with pytest.raises(MacieException, match="Cannot compile"):
        reut.compile(pattern=r"a{2,1}")


def test_macie_regex_bad_input() -> None:
    with pytest.raises(TypeError):
        reut.compile(pattern=None)
    with pytest.raises(ValueError):
        reut.compile(pattern="")
    with pytest.raises(TypeError):
        reut.to_python(pattern=1)
