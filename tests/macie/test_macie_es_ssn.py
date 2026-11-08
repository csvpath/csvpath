"""SPAIN_SOCIAL_SECURITY_NUMBER: the 12 digit affiliation number (NAF),
format only (FormatDetector). Missed by the first inventory, found when
building the recommended-list assets (2026-11-08)."""

import pytest

from csvpath.macie.allow_list_set import AllowListSet
from csvpath.macie.detectors.format_detector import FormatDetector
from csvpath.macie.managed_catalog import ManagedCatalog
from csvpath.macie.managed_identifier import ManagedIdentifier
from csvpath.macie.recommended_lists import RecommendedLists
from csvpath.macie.severity_levels import SeverityLevels

NO_ALLOW = AllowListSet()
NAME = "SPAIN_SOCIAL_SECURITY_NUMBER"


@pytest.fixture(scope="module")
def catalog() -> ManagedCatalog:
    return ManagedCatalog.load()


def _mdi(catalog) -> ManagedIdentifier:
    e = catalog.identifier(name=NAME)
    return ManagedIdentifier(
        name=NAME,
        category=e["category"],
        detector=e["detector"],
        keyword_mode=e["keyword_mode"],
        keywords=e["keywords"],
        distance=e["distance"],
        severity=SeverityLevels.parse(text=e["severity"]),
        catalog=catalog,
    )


@pytest.mark.parametrize(
    "cell", ["281234567840", "28/12345678/40", "28 12345678 40", "28-12345678-40"]
)
def test_macie_es_ssn_formats(catalog, cell: str) -> None:
    d = FormatDetector(config=catalog.detector(name="es_ssn"))
    assert d.matches(cell=cell) == [(0, len(cell))]


@pytest.mark.parametrize(
    "cell",
    [
        #
        # province 00; mixed separators; too long or short
        #
        "001234567840",
        "28/12345678-40",
        "2812345678401",
        "28123456784",
    ],
)
def test_macie_es_ssn_not_detected(catalog, cell: str) -> None:
    d = FormatDetector(config=catalog.detector(name="es_ssn"))
    assert d.matches(cell=cell) == []


def test_macie_es_ssn_catalog(catalog) -> None:
    e = catalog.identifier(name=NAME)
    assert e["category"] == "PERSONAL_INFORMATION"
    assert e["keyword_mode"] == "required"
    assert e["severity"] == "1:HIGH"
    assert e["fidelity"] == "B"
    assert "número de la seguridad social" in e["keywords"]
    #
    # it is in Macie's recommended sets, which is how its absence was found
    #
    assert NAME in RecommendedLists.for_job()[0]


@pytest.mark.parametrize(
    "cell, header, n",
    [
        ("número de la seguridad social 28/12345678/40", "x", 1),
        ("28/12345678/40", "ssn", 1),
        ("28/12345678/40", "notes", 0),
        #
        # a US SSN near "ssn" is not a Spanish one: the shapes differ
        #
        ("ssn 123-45-6789", "x", 0),
    ],
)
def test_macie_es_ssn_identifier(catalog, cell: str, header: str, n: int) -> None:
    assert (
        _mdi(catalog).occurrences(cell=cell, header=header, allow_lists=NO_ALLOW) == n
    )
