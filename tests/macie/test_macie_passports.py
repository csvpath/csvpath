"""Passport number stand-ins, the second group B step: seven countries'
formats in FormatDetector's notation, and the catalog entries."""

import pytest

from csvpath.macie.allow_list_set import AllowListSet
from csvpath.macie.detectors.format_detector import FormatDetector
from csvpath.macie.managed_catalog import ManagedCatalog
from csvpath.macie.managed_identifier import ManagedIdentifier
from csvpath.macie.severity_levels import SeverityLevels

NO_ALLOW = AllowListSet()
COUNTRIES = ["CANADA", "FRANCE", "GERMANY", "ITALY", "SPAIN", "UK", "USA"]


@pytest.fixture(scope="module")
def catalog() -> ManagedCatalog:
    return ManagedCatalog.load()


def _detector(catalog, country: str) -> FormatDetector:
    return FormatDetector(config=catalog.detector(name=f"{country.lower()}_passport"))


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
    "country, cell",
    [
        ("CANADA", "AB123456"),
        ("CANADA", "gk987654"),
        ("FRANCE", "12AB34567"),
        ("GERMANY", "C01X00T47"),
        ("GERMANY", "K9876543Z"),
        ("ITALY", "YA1234567"),
        ("SPAIN", "PAA123456"),
        ("SPAIN", "AB123456"),
        ("UK", "123456789"),
        ("USA", "123456789"),
        ("USA", "A12345678"),
    ],
)
def test_macie_passport_formats(catalog, country: str, cell: str) -> None:
    assert _detector(catalog, country).matches(cell=cell) == [(0, len(cell))]


@pytest.mark.parametrize(
    "country, cell",
    [
        ("CANADA", "A1234567"),
        ("CANADA", "AB1234567"),
        ("FRANCE", "AB1234567"),
        ("FRANCE", "12A345678"),
        #
        # Germany: no vowels, no B D Q S, and a first letter C F G H J K
        #
        ("GERMANY", "A01X00T47"),
        ("GERMANY", "C01X00E47"),
        ("GERMANY", "L01X00T47"),
        ("GERMANY", "C01X00T4"),
        ("ITALY", "Y1234567"),
        ("ITALY", "YA12345678"),
        ("SPAIN", "PAAA12345"),
        ("UK", "12345678"),
        ("UK", "A12345678"),
        ("USA", "AB1234567"),
        ("USA", "1234567890"),
    ],
)
def test_macie_passport_not_detected(catalog, country: str, cell: str) -> None:
    assert _detector(catalog, country).matches(cell=cell) == []


def test_macie_passport_catalog(catalog) -> None:
    for c in COUNTRIES:
        e = catalog.identifier(name=f"{c}_PASSPORT_NUMBER")
        assert e["category"] == "PERSONAL_INFORMATION"
        assert e["keyword_mode"] == "required"
        #
        # Macie: passport numbers are MEDIUM for one, HIGH from two
        #
        assert e["severity"] == "1:MEDIUM 2:HIGH"
    assert catalog.identifier(name="USA_PASSPORT_NUMBER")["keywords"] == [
        "passport",
        "travel document",
    ]
    assert (
        "reisepassnummer"
        in catalog.identifier(name="GERMANY_PASSPORT_NUMBER")["keywords"]
    )


@pytest.mark.parametrize(
    "name, cell, header, n",
    [
        ("CANADA_PASSPORT_NUMBER", "AB123456", "passport", 1),
        ("FRANCE_PASSPORT_NUMBER", "numéro de passeport 12AB34567", "x", 1),
        ("GERMANY_PASSPORT_NUMBER", "C01X00T47", "reisepassnummer", 1),
        ("ITALY_PASSPORT_NUMBER", "passaporto YA1234567", "x", 1),
        ("SPAIN_PASSPORT_NUMBER", "PAA123456", "pasaporte", 1),
        ("USA_PASSPORT_NUMBER", "travel document A12345678", "x", 1),
        ("USA_PASSPORT_NUMBER", "A12345678", "notes", 0),
        #
        # 9 digits near "passport number" is both a UK and a US number:
        # both formats are 9 digits and both lists have the keyword
        #
        ("UK_PASSPORT_NUMBER", "passport number 123456789", "x", 1),
        ("USA_PASSPORT_NUMBER", "passport number 123456789", "x", 1),
        #
        # but the UK list does not have the bare "passport"
        #
        ("UK_PASSPORT_NUMBER", "passport 123456789", "x", 0),
    ],
)
def test_macie_passport_identifiers(
    catalog, name: str, cell: str, header: str, n: int
) -> None:
    assert (
        _mdi(catalog, name).occurrences(cell=cell, header=header, allow_lists=NO_ALLOW)
        == n
    )
