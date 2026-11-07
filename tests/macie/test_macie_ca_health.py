"""Canada health numbers, a group A leftover: CaHealthDetector's British
Columbia, Ontario and Quebec forms, and the catalog entry. The BC check is
also compared with python-stdnum in test_macie_checksum_oracle.py."""

import pytest

from csvpath.macie.allow_list_set import AllowListSet
from csvpath.macie.util.checksum_utility import ChecksumUtility as chut
from csvpath.macie.detectors.ca_health_detector import CaHealthDetector
from csvpath.macie.managed_catalog import ManagedCatalog
from csvpath.macie.managed_identifier import ManagedIdentifier
from csvpath.macie.severity_levels import SeverityLevels

NO_ALLOW = AllowListSet()
DETECTOR = CaHealthDetector(config={})


@pytest.fixture(scope="module")
def catalog() -> ManagedCatalog:
    return ManagedCatalog.load()


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


def test_macie_ca_bc_phn_check() -> None:
    #
    # python-stdnum's documented example; a BC PHN starts with 9
    #
    assert chut.ca_bc_phn(digits="9698658215") is True
    assert chut.ca_bc_phn(digits="9698658216") is False
    assert chut.ca_bc_phn(digits="1698658215") is False
    with pytest.raises(ValueError):
        chut.ca_bc_phn(digits="969865821")
    with pytest.raises(TypeError):
        chut.ca_bc_phn(digits=None)


@pytest.mark.parametrize(
    "cell",
    [
        #
        # British Columbia
        #
        "9698658215",
        "9698 658 215",
        "9698-658-215",
        #
        # Ontario, with and without a version code
        #
        "1234567897",
        "1234-567-897",
        "1234 567 897 AB",
        "1234567897A",
        #
        # Quebec: a woman born 1965-03-15 (month 53), and a man
        #
        "TREJ 6553 1512",
        "TREJ65031512",
    ],
)
def test_macie_ca_health_forms(cell: str) -> None:
    assert DETECTOR.matches(cell=cell) == [(0, len(cell))]


@pytest.mark.parametrize(
    "cell",
    [
        #
        # a failed BC or Luhn check; mixed separators; touching letters or
        # digits; a RAMQ month that is not 01-12 or 51-62; a day that does
        # not exist
        #
        "9698658216",
        "1234567890",
        "1234-567 897",
        "x1234567897",
        "12345678970",
        "TREJ 6563 1512",
        "TREJ 6513 1512",
        "TREJ 6502 3012",
    ],
)
def test_macie_ca_health_not_detected(cell: str) -> None:
    assert DETECTOR.matches(cell=cell) == []


def test_macie_ca_health_one_occurrence() -> None:
    #
    # a BC PHN can also pass Luhn; it is one number
    #
    assert chut.luhn(digits="9876543217") and not chut.ca_bc_phn(digits="9876543217")
    assert chut.ca_bc_phn(digits="9876543218")
    assert DETECTOR.matches(cell="phn 9876543218, ON 1234567897") == [
        (4, 14),
        (19, 29),
    ]


def test_macie_ca_health_bad_input() -> None:
    with pytest.raises(TypeError):
        CaHealthDetector(config=None)
    with pytest.raises(TypeError):
        DETECTOR.matches(cell=None)


def test_macie_ca_health_catalog(catalog) -> None:
    e = catalog.identifier(name="CANADA_HEALTH_NUMBER")
    assert e["category"] == "PERSONAL_INFORMATION"
    assert e["keyword_mode"] == "required"
    #
    # Macie: health insurance or medical identification numbers are HIGH
    # from one occurrence
    #
    assert e["severity"] == "1:HIGH"
    assert e["keywords"] == [
        "canada healthcare number",
        "msp number",
        "personal healthcare number",
        "phn",
        "soins de santé",
    ]


@pytest.mark.parametrize(
    "cell, header, n",
    [
        ("9698 658 215", "phn", 1),
        ("msp number 9698658215", "x", 1),
        ("soins de santé TREJ 6553 1512", "x", 1),
        ("9698 658 215", "notes", 0),
        #
        # "health card" is not one of Macie's Canada keywords
        #
        ("health card 1234567897", "x", 0),
    ],
)
def test_macie_ca_health_identifier(catalog, cell: str, header: str, n: int) -> None:
    assert (
        _mdi(catalog, "CANADA_HEALTH_NUMBER").occurrences(
            cell=cell, header=header, allow_lists=NO_ALLOW
        )
        == n
    )
