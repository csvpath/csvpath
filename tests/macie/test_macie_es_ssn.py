"""SPAIN_SOCIAL_SECURITY_NUMBER: the 12 digit affiliation number (NAF),
with its control digits checked (GroupedDigitsDetector, check es_naf):
the seventh live probe (2026-11-18) found Macie checks them. Missed by
the first inventory, found when building the recommended-list assets
(2026-11-08)."""

import pytest

from csvpath.macie.allow_list_set import AllowListSet
from csvpath.macie.detectors.grouped_digits_detector import GroupedDigitsDetector
from csvpath.macie.util.checksum_utility import ChecksumUtility as chut
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
    d = GroupedDigitsDetector(config=catalog.detector(name="es_ssn"))
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
        #
        # control digits wrong
        #
        "281234567841",
        "28/12345678/41",
    ],
)
def test_macie_es_ssn_not_detected(catalog, cell: str) -> None:
    d = GroupedDigitsDetector(config=catalog.detector(name="es_ssn"))
    assert d.matches(cell=cell) == []


def test_macie_es_naf() -> None:
    assert chut.es_naf(digits="281234567840")
    assert not chut.es_naf(digits="281234567841")
    #
    # province 00 is never valid
    #
    assert not chut.es_naf(digits="000000000000")
    #
    # a number below 10,000,000: either published way of computing it
    #
    plain = "2801234567" + f"{int('2801234567') % 97:02d}"
    other = "2801234567" + f"{(28 * 10_000_000 + 1234567) % 97:02d}"
    assert chut.es_naf(digits=plain)
    assert chut.es_naf(digits=other)
    with pytest.raises(ValueError):
        chut.es_naf(digits="28123456784")
    with pytest.raises(TypeError):
        chut.es_naf(digits=None)


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
