"""FormatDetector and its format notation, then the first group B stand-ins
written in it: UK National Insurance number, US and Canada bank account
number, and card security code."""

import pytest

from csvpath.macie.allow_list_set import AllowListSet
from csvpath.macie.detectors.format_detector import FormatDetector
from csvpath.macie.macie_exceptions import MacieException
from csvpath.macie.managed_catalog import ManagedCatalog
from csvpath.macie.managed_identifier import ManagedIdentifier
from csvpath.macie.severity_levels import SeverityLevels

NO_ALLOW = AllowListSet()


def _finds(formats: list, cell: str, **extra) -> list[tuple[int, int]]:
    return FormatDetector(config={"formats": formats, **extra}).matches(cell=cell)


# =============
# the notation
# =============


@pytest.mark.parametrize(
    "fmt, yes, no",
    [
        ("###", "123", "12a"),
        ("AAA", "aBc", "ab1"),
        ("XXX", "a1B", "a-1"),
        ("[ABC]#", "b7", "d7"),
        ("[A-CX]#", "x7", "d7"),
        ("[0-3]#", "27", "47"),
        ("#{4}", "1234", "123"),
        ("A#{2,3}", "a123", "a1"),
        ("##-##", "12-34", "12 34"),
        ("## ##", "12 34", "12-34"),
        ("9##", "912", "812"),
        ("[L]#", "l5", "k5"),
    ],
)
def test_macie_format_notation(fmt: str, yes: str, no: str) -> None:
    assert _finds([fmt], yes) == [(0, len(yes))]
    assert _finds([fmt], no) == []


@pytest.mark.parametrize(
    "fmt",
    [
        "",
        "  ",
        "AIza",
        "#{0}",
        "#{3,2}",
        "#{a}",
        "{3}",
        "[A",
        "A]",
        "[]",
        "[A-]",
        "[C-A]",
        "[A-9]",
        "[%]",
        "#}",
    ],
)
def test_macie_format_notation_errors(fmt: str) -> None:
    #
    # any letter but A or X must be in a set, so AIza fails
    #
    with pytest.raises(MacieException):
        FormatDetector(config={"formats": [fmt]})


def test_macie_format_compiles_once_and_dedupes() -> None:
    d = FormatDetector(config={"formats": ["#{3}", "###", {"format": "#{3}"}]})
    assert d.candidates.pattern.count("[0-9]{3}") == 1
    assert d.candidates.pattern.count("[0-9][0-9][0-9]") == 1


def test_macie_format_boundaries() -> None:
    assert _finds(["#{3}"], "x123") == []
    assert _finds(["#{3}"], "1234") == []
    assert _finds(["#{3}"], "id 123, 456.") == [(3, 6), (8, 11)]


def test_macie_format_alternatives_backtrack() -> None:
    #
    # a shorter format that would touch a digit gives way to a longer one
    #
    assert _finds(["#{3}", "#{5}"], "12345") == [(0, 5)]


def test_macie_format_used_by_entries() -> None:
    d = FormatDetector(
        config={"formats": [{"format": "A#{7}", "used_by": ["CA", "NY"]}, "#{9}"]}
    )
    assert d.matches(cell="A1234567") == [(0, 8)]
    for bad in [
        {"format": "A#{7}", "states": ["CA"]},
        {"format": "A#{7}", "used_by": "CA"},
        {"format": "A#{7}", "used_by": [""]},
        {"used_by": ["CA"]},
        7,
    ]:
        with pytest.raises(MacieException):
            FormatDetector(config={"formats": [bad]})


def test_macie_format_exclusions_and_prefixes() -> None:
    config = {
        "formats": ["AA ## ##"],
        "exclusions": ["ab 12 34"],
        "exclude_prefixes": ["ZZ"],
    }
    d = FormatDetector(config=config)
    assert d.matches(cell="AB 12 34") == []
    assert d.matches(cell="zz 56 78") == []
    assert d.matches(cell="AC 12 34") == [(0, 8)]


def test_macie_format_bad_config() -> None:
    with pytest.raises(TypeError):
        FormatDetector(config=None)
    for bad in [
        {},
        {"formats": []},
        {"formats": "###"},
        {"formats": ["###"], "exclusions": "x"},
    ]:
        with pytest.raises(MacieException):
            FormatDetector(config=bad)
    with pytest.raises(TypeError):
        FormatDetector(config={"formats": ["###"]}).matches(cell=None)


# =============
# the first entries
# =============


@pytest.fixture(scope="module")
def catalog() -> ManagedCatalog:
    return ManagedCatalog.load()


def _detector(catalog, name: str) -> FormatDetector:
    return FormatDetector(config=catalog.detector(name=name))


def _mdi(catalog, name: str) -> ManagedIdentifier:
    e = catalog.identifier(name=name)
    return ManagedIdentifier(
        name=name,
        category=e["category"],
        detector=e["detector"],
        keyword_mode=e["keyword_mode"],
        keywords=e["keywords"],
        distance=e["distance"],
        severity=SeverityLevels.parse(text=e["severity"]),
        catalog=catalog,
    )


@pytest.mark.parametrize(
    "cell", ["AB123456C", "AB 12 34 56 C", "ab123456d", "ZY123456A", "CE987654B"]
)
def test_macie_nino_formats(catalog, cell: str) -> None:
    assert _detector(catalog, "gb_nino").matches(cell=cell) == [(0, len(cell))]


@pytest.mark.parametrize(
    "cell",
    [
        #
        # HMRC: D F I Q U V never a prefix letter; O never the second;
        # BG GB KN NK NT TN ZZ not used; the suffix is A to D
        #
        "DA123456A",
        "AD123456A",
        "QQ123456A",
        "AO123456A",
        "GB123456A",
        "NK123456A",
        "ZZ123456A",
        "AB123456E",
        "AB12345C",
        "AB 123456 C",
        "AB 12 3456 C",
    ],
)
def test_macie_nino_not_detected(catalog, cell: str) -> None:
    assert _detector(catalog, "gb_nino").matches(cell=cell) == []


@pytest.mark.parametrize(
    "cell, found",
    [
        ("123456789", True),
        ("12345678901234567", True),
        ("12345678", False),
        ("123456789012345678", False),
        ("1234 5678 9012", False),
    ],
)
def test_macie_bank_account_format(catalog, cell: str, found: bool) -> None:
    #
    # Macie: 9-17 digits without spaces
    #
    expected = [(0, len(cell))] if found else []
    assert _detector(catalog, "bank_account").matches(cell=cell) == expected


@pytest.mark.parametrize(
    "cell, found",
    [("123", True), ("1234", True), ("12", False), ("12345", False)],
)
def test_macie_card_security_code_format(catalog, cell: str, found: bool) -> None:
    expected = [(0, len(cell))] if found else []
    assert _detector(catalog, "card_security_code").matches(cell=cell) == expected


def test_macie_group_b_first_catalog(catalog) -> None:
    nino = catalog.identifier(name="UK_NATIONAL_INSURANCE_NUMBER")
    bank = catalog.identifier(name="BANK_ACCOUNT_NUMBER")
    cvv = catalog.identifier(name="CREDIT_CARD_SECURITY_CODE")
    assert nino["category"] == "PERSONAL_INFORMATION"
    assert bank["category"] == cvv["category"] == "FINANCIAL_INFORMATION"
    assert nino["severity"] == bank["severity"] == "1:HIGH"
    #
    # Macie: verification codes are MEDIUM for one occurrence, HIGH from two
    #
    assert cvv["severity"] == "1:MEDIUM 2:HIGH"
    assert "nino" in nino["keywords"]
    assert "chequing account" in bank["keywords"]
    assert "cvv2" in cvv["keywords"]


@pytest.mark.parametrize(
    "name, cell, header, n",
    [
        ("UK_NATIONAL_INSURANCE_NUMBER", "AB 12 34 56 C", "nino", 1),
        ("UK_NATIONAL_INSURANCE_NUMBER", "AB123456C", "notes", 0),
        ("BANK_ACCOUNT_NUMBER", "chequing account 000123456789", "x", 1),
        ("BANK_ACCOUNT_NUMBER", "000123456789", "notes", 0),
        ("CREDIT_CARD_SECURITY_CODE", "cvv 123", "x", 1),
        ("CREDIT_CARD_SECURITY_CODE", "123", "notes", 0),
        #
        # the keyword cvv2 holds a digit, but a lone 2 is not a code
        #
        ("CREDIT_CARD_SECURITY_CODE", "cvv2: 4321", "x", 1),
    ],
)
def test_macie_group_b_first_identifiers(
    catalog, name: str, cell: str, header: str, n: int
) -> None:
    assert (
        _mdi(catalog, name).occurrences(cell=cell, header=header, allow_lists=NO_ALLOW)
        == n
    )
