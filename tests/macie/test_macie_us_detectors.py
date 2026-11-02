"""the US SSN and NPI detectors, and their catalog entries. Macie
publishes only these identifiers' keywords; the formats are from SSA and
CMS. The valid NPIs pass Luhn over 80840 + the first nine digits, checked
outside ChecksumUtility."""

import pytest

from csvpath.macie.allow_list_set import AllowListSet
from csvpath.macie.detectors.us_npi_detector import UsNpiDetector
from csvpath.macie.detectors.us_ssn_detector import UsSsnDetector
from csvpath.macie.macie_exceptions import MacieException
from csvpath.macie.managed_catalog import ManagedCatalog
from csvpath.macie.managed_identifier import ManagedIdentifier
from csvpath.macie.severity_levels import SeverityLevels

NO_ALLOW = AllowListSet()


@pytest.fixture(scope="module")
def catalog() -> ManagedCatalog:
    return ManagedCatalog.load()


@pytest.fixture(scope="module")
def ssn(catalog) -> UsSsnDetector:
    return UsSsnDetector(config=catalog.detector(name="us_ssn"))


@pytest.fixture(scope="module")
def npi(catalog) -> UsNpiDetector:
    return UsNpiDetector(config=catalog.detector(name="us_npi"))


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


# =============
# SSN
# =============


@pytest.mark.parametrize(
    "cell", ["123-45-6789", "123 45 6789", "123456789", "665-01-0001"]
)
def test_macie_ssn_formats(ssn, cell: str) -> None:
    assert ssn.matches(cell=cell) == [(0, len(cell))]


@pytest.mark.parametrize(
    "cell",
    [
        "000-12-3456",
        "666-12-3456",
        "900-12-3456",
        "987-65-4321",
        "123-00-4567",
        "123-45-0000",
    ],
)
def test_macie_ssn_never_issued(ssn, cell: str) -> None:
    assert ssn.matches(cell=cell) == []


@pytest.mark.parametrize("cell", ["078-05-1120", "219 09 9999", "457555462"])
def test_macie_ssn_published_examples_are_excluded(ssn, cell: str) -> None:
    assert ssn.matches(cell=cell) == []


@pytest.mark.parametrize(
    "cell",
    ["123-45 6789", "12-345-6789", "123-456-789", "1234-56-789", "123.45.6789"],
)
def test_macie_ssn_irregular_layouts(ssn, cell: str) -> None:
    assert ssn.matches(cell=cell) == []


def test_macie_ssn_boundaries_and_several(ssn) -> None:
    assert ssn.matches(cell="1123-45-6789") == []
    assert ssn.matches(cell="123-45-67890") == []
    assert ssn.matches(cell="1234567890") == []
    assert ssn.matches(cell="a 123-45-6789; 234 56 7890") == [(2, 13), (15, 26)]


def test_macie_ssn_bad_config() -> None:
    with pytest.raises(TypeError):
        UsSsnDetector(config=None)
    with pytest.raises(MacieException):
        UsSsnDetector(config={"exclusions": ["123-45-6789"]})
    with pytest.raises(MacieException):
        UsSsnDetector(config={"exclusions": "078051120"})


def test_macie_ssn_identifier(catalog) -> None:
    e = catalog.identifier(name="USA_SOCIAL_SECURITY_NUMBER")
    assert e["category"] == "PERSONAL_INFORMATION"
    assert e["keywords"] == ["social security", "ss#", "ssn"]
    assert e["severity"] == "1:HIGH"
    mdi = _mdi(catalog, "USA_SOCIAL_SECURITY_NUMBER")
    assert mdi.occurrences(cell="123-45-6789", header="ssn", allow_lists=NO_ALLOW) == 1
    assert (
        mdi.occurrences(cell="SS# 123-45-6789", header="x", allow_lists=NO_ALLOW) == 1
    )
    assert mdi.occurrences(cell="123-45-6789", header="x", allow_lists=NO_ALLOW) == 0


# =============
# NPI
# =============


@pytest.mark.parametrize("cell", ["1234567893", "2987654326"])
def test_macie_npi_valid(npi, cell: str) -> None:
    assert npi.matches(cell=cell) == [(0, 10)]


@pytest.mark.parametrize(
    "cell",
    [
        #
        # bad check digit
        #
        "1234567890",
        "2987654327",
        #
        # must start with 1 or 2
        #
        "3234567893",
        #
        # 9 and 11 digits
        #
        "123456789",
        "12345678930",
        #
        # NPIs are not written with separators
        #
        "123-456-7893",
    ],
)
def test_macie_npi_invalid(npi, cell: str) -> None:
    assert npi.matches(cell=cell) == []


def test_macie_npi_boundaries_and_several(npi) -> None:
    assert npi.matches(cell="91234567893") == []
    assert npi.matches(cell="npi 1234567893, alt 2987654326") == [(4, 14), (20, 30)]


def test_macie_npi_exclusions_and_bad_config() -> None:
    assert (
        UsNpiDetector(config={"exclusions": ["1234567893"]}).matches(cell="1234567893")
        == []
    )
    with pytest.raises(TypeError):
        UsNpiDetector(config=None)
    with pytest.raises(MacieException):
        UsNpiDetector(config={"exclusions": ["123456789"]})


def test_macie_npi_identifier(catalog) -> None:
    e = catalog.identifier(name="USA_NATIONAL_PROVIDER_IDENTIFIER")
    assert e["category"] == "PERSONAL_INFORMATION"
    assert e["keywords"] == ["hipaa", "n.p.i", "national provider", "npi"]
    mdi = _mdi(catalog, "USA_NATIONAL_PROVIDER_IDENTIFIER")
    assert (
        mdi.occurrences(cell="1234567893", header="provider_npi", allow_lists=NO_ALLOW)
        == 1
    )
    assert mdi.occurrences(cell="1234567893", header="x", allow_lists=NO_ALLOW) == 0
