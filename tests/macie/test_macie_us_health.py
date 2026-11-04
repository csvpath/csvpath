"""US health and taxpayer stand-ins on UsIdDetector: DEA, Medicare MBI,
ITIN, HICN, NDC and HCPCS, the DEA check, and the catalog entries."""

import pytest

from csvpath.macie.allow_list_set import AllowListSet
from csvpath.macie.checksum_utility import ChecksumUtility as chut
from csvpath.macie.detectors.us_id_detector import UsIdDetector
from csvpath.macie.macie_converter import MacieConverter
from csvpath.macie.macie_exceptions import MacieException
from csvpath.macie.macie_wrapper_loader import MacieWrapperLoader
from csvpath.macie.managed_catalog import ManagedCatalog
from csvpath.macie.managed_identifier import ManagedIdentifier
from csvpath.macie.severity_levels import SeverityLevels

NO_ALLOW = AllowListSet()
NAMES = [
    "US_DRUG_ENFORCEMENT_AGENCY_NUMBER",
    "USA_MEDICARE_BENEFICIARY_IDENTIFIER",
    "USA_INDIVIDUAL_TAX_IDENTIFICATION_NUMBER",
    "USA_HEALTH_INSURANCE_CLAIM_NUMBER",
    "USA_NATIONAL_DRUG_CODE",
    "USA_HEALTHCARE_PROCEDURE_CODE",
]


@pytest.fixture(scope="module")
def catalog() -> ManagedCatalog:
    return ManagedCatalog.load()


def _detector(catalog, name: str) -> UsIdDetector:
    return UsIdDetector(config=catalog.detector(name=name))


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
    "digits, ok",
    [
        #
        # the textbook example AB1234563: 1+3+5 + 2*(2+4+6) = 33
        #
        ("1234563", True),
        ("1234564", False),
        ("9876547", True),
        ("0000000", True),
    ],
)
def test_macie_us_dea_check(digits: str, ok: bool) -> None:
    assert chut.us_dea(digits=digits) is ok


def test_macie_us_dea_check_bad_input() -> None:
    for bad in ["123456", "12345678", "123456a"]:
        with pytest.raises(ValueError):
            chut.us_dea(digits=bad)


@pytest.mark.parametrize(
    "name, cell",
    [
        ("us_dea", "AB1234563"),
        ("us_dea", "FB9876547"),
        ("us_dea", "A91234563"),
        ("us_dea", "ab1234563"),
        ("us_mbi", "2AC3-DE4-FG56"),
        ("us_mbi", "2AC3DE4FG56"),
        ("us_mbi", "2ac3de4fg56"),
        ("us_mbi", "9Y99Y99YY99"),
        ("us_itin", "912-90-3456"),
        ("us_itin", "912 70 1234"),
        ("us_itin", "912881234"),
        #
        # the middle ranges the IRS added in 2011
        #
        ("us_itin", "912-55-3456"),
        ("us_itin", "912-65-3456"),
        ("us_hicn", "123-45-6789A"),
        ("us_hicn", "123456789B1"),
        ("us_hicn", "123-45-6789-A"),
        ("us_hicn", "123 45 6789 HA"),
        ("us_ndc", "0002-1433-80"),
        ("us_ndc", "50580-506-02"),
        ("us_ndc", "12345-6789-1"),
        ("us_ndc", "12345-6789-01"),
        ("us_ndc", "1234567890"),
        ("us_ndc", "12345678901"),
        ("us_hcpcs", "J1234"),
        ("us_hcpcs", "e0601"),
        ("us_hcpcs", "99213"),
        ("us_hcpcs", "0001F"),
    ],
)
def test_macie_us_health_formats(catalog, name: str, cell: str) -> None:
    assert _detector(catalog, name).matches(cell=cell) == [(0, len(cell))]


@pytest.mark.parametrize(
    "name, cell",
    [
        ("us_dea", "AB1234564"),
        ("us_dea", "AB123456"),
        ("us_dea", "1B1234563"),
        ("us_dea", "XAB1234563"),
        #
        # CMS's published example; an S; a leading 0; a letter where a
        # digit goes; one dash
        #
        ("us_mbi", "1EG4-TE5-MK73"),
        ("us_mbi", "2SC3DE4FG56"),
        ("us_mbi", "0AC3DE4FG56"),
        ("us_mbi", "2AC3DE4FGA6"),
        ("us_mbi", "2AC3-DE4FG56"),
        ("us_itin", "912-89-3456"),
        ("us_itin", "912-93-4567"),
        ("us_itin", "912-66-1234"),
        ("us_itin", "912-70 1234"),
        ("us_itin", "812-70-1234"),
        ("us_hicn", "000-45-6789A"),
        ("us_hicn", "123-45-6789"),
        ("us_hicn", "123-45-6789ABC"),
        ("us_ndc", "123-4567-89"),
        ("us_ndc", "123456789"),
        ("us_ndc", "123456789012"),
        ("us_ndc", "0002-1433-80-1"),
        ("us_hcpcs", "W1234"),
        ("us_hcpcs", "J12345"),
        ("us_hcpcs", "1234"),
    ],
)
def test_macie_us_health_not_detected(catalog, name: str, cell: str) -> None:
    assert _detector(catalog, name).matches(cell=cell) == []


def test_macie_us_id_bad_config() -> None:
    with pytest.raises(TypeError):
        UsIdDetector(config=None)
    for bad in [{}, {"form": "npi"}, {"form": "dea", "exclusions": "x"}]:
        with pytest.raises(MacieException):
            UsIdDetector(config=bad)
    with pytest.raises(TypeError):
        UsIdDetector(config={"form": "dea"}).matches(cell=None)


def test_macie_us_health_catalog(catalog) -> None:
    for n in NAMES:
        e = catalog.identifier(name=n)
        assert e["category"] == "PERSONAL_INFORMATION"
        assert e["keyword_mode"] == "required"
        assert e["severity"] == "1:HIGH"
    hicn = catalog.identifier(name="USA_HEALTH_INSURANCE_CLAIM_NUMBER")
    assert "Railroad" in hicn["partial"]
    assert catalog.identifier(name="USA_MEDICARE_BENEFICIARY_IDENTIFIER")[
        "keywords"
    ] == ["mbi", "medicare beneficiary"]


@pytest.mark.parametrize(
    "name, cell, header, n",
    [
        ("US_DRUG_ENFORCEMENT_AGENCY_NUMBER", "AB1234563", "dea_number", 1),
        ("US_DRUG_ENFORCEMENT_AGENCY_NUMBER", "AB1234563", "notes", 0),
        ("USA_MEDICARE_BENEFICIARY_IDENTIFIER", "MBI 2AC3-DE4-FG56", "x", 1),
        ("USA_INDIVIDUAL_TAX_IDENTIFICATION_NUMBER", "912-90-3456", "itin", 1),
        ("USA_HEALTH_INSURANCE_CLAIM_NUMBER", "hicn 123-45-6789A", "x", 1),
        ("USA_NATIONAL_DRUG_CODE", "0002-1433-80", "ndc", 1),
        ("USA_HEALTHCARE_PROCEDURE_CODE", "J1234", "hcpcs_code", 1),
        ("USA_HEALTHCARE_PROCEDURE_CODE", "J1234", "notes", 0),
    ],
)
def test_macie_us_health_identifiers(
    catalog, name: str, cell: str, header: str, n: int
) -> None:
    assert (
        _mdi(catalog, name).occurrences(cell=cell, header=header, allow_lists=NO_ALLOW)
        == n
    )


def test_macie_us_health_converter_reports_hicn_partial() -> None:
    w = MacieWrapperLoader.from_path(
        path="tests/macie/test_resources/wrappers/handcrafted_minimal.macie.json"
    )
    w["selection"]["managedDataIdentifierIds"] = list(NAMES)
    w["managedDataIdentifiers"]["resolved"] = list(NAMES)
    skipped = MacieConverter(wrapper=w).convert(name="t").report.skipped
    assert [(s.location, s.feature) for s in skipped] == [
        ("managedDataIdentifiers.resolved[3]", "managedDataIdentifier.partial")
    ]
