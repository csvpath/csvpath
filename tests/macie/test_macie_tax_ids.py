"""Germany Steuer-IdNr, Argentina CUIT/CUIL, Australia TFN and UK UTR
stand-ins: the checks, GroupedDigitsDetector's data for each, and the
catalog entries. test_macie_checksum_oracle compares the checks with
python-stdnum on random inputs; the published examples here are stdnum's."""

import pytest

from csvpath.macie.allow_list_set import AllowListSet
from csvpath.macie.checksum_utility import ChecksumUtility as chut
from csvpath.macie.detectors.grouped_digits_detector import GroupedDigitsDetector
from csvpath.macie.macie_converter import MacieConverter
from csvpath.macie.macie_wrapper_loader import MacieWrapperLoader
from csvpath.macie.managed_catalog import ManagedCatalog
from csvpath.macie.managed_identifier import ManagedIdentifier
from csvpath.macie.severity_levels import SeverityLevels

NO_ALLOW = AllowListSet()
IDNR = "36574261809"
CUIT = "20055361682"
CUIT_ORG = "30712345671"
TFN = "123456782"
UTR = "1955839661"


@pytest.fixture(scope="module")
def catalog() -> ManagedCatalog:
    return ManagedCatalog.load()


def _detector(catalog, name: str) -> GroupedDigitsDetector:
    return GroupedDigitsDetector(config=catalog.detector(name=name))


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
# checks
# =============


@pytest.mark.parametrize(
    "n, ok",
    [
        (IDNR, True),
        ("36574261890", False),
        #
        # one digit twice, or three times, in the first ten
        #
        ("47893125709", True),
        ("47773125600", True),
        #
        # right MOD 11,10 digit, but: a leading 0; two digits repeated;
        # no digit repeated; one digit four times
        #
        ("06574261803", False),
        ("36554266806", False),
        ("12345678903", False),
        ("47777125605", False),
    ],
)
def test_macie_de_idnr(n: str, ok: bool) -> None:
    assert chut.de_idnr(digits=n) is ok


@pytest.mark.parametrize(
    "n, ok",
    [
        (CUIT, True),
        ("20267565393", True),
        ("20267565392", False),
        (CUIT_ORG, True),
        ("50000000016", True),
    ],
)
def test_macie_ar_cuit(n: str, ok: bool) -> None:
    assert chut.ar_cuit(digits=n) is ok


@pytest.mark.parametrize("n, ok", [(TFN, True), ("999999999", False)])
def test_macie_au_tfn(n: str, ok: bool) -> None:
    assert chut.au_tfn(digits=n) is ok


@pytest.mark.parametrize(
    "n, ok", [(UTR, True), ("2955839661", False), ("2234567890", True)]
)
def test_macie_gb_utr(n: str, ok: bool) -> None:
    #
    # the check digit is the first, not the last
    #
    assert chut.gb_utr(digits=n) is ok


def test_macie_tax_checks_bad_input() -> None:
    for check, n in [
        (chut.de_idnr, "3657426180"),
        (chut.ar_cuit, "2005536168"),
        (chut.au_tfn, "12345678"),
        (chut.gb_utr, "195583966"),
        (chut.gb_utr, "195583966a"),
    ]:
        with pytest.raises(ValueError):
            check(digits=n)
    with pytest.raises(TypeError):
        chut.de_idnr(digits=None)
    for name in ["de_idnr", "ar_cuit", "au_tfn", "gb_utr"]:
        assert name in chut.CHECKS


# =============
# detectors
# =============


@pytest.mark.parametrize(
    "name, cell",
    [
        ("de_idnr", IDNR),
        ("de_idnr", "36 574 261 809"),
        ("de_idnr", "36-574-261-809"),
        ("ar_cuit_individual", "20-05536168-2"),
        ("ar_cuit_individual", "20 05536168 2"),
        ("ar_cuit_individual", CUIT),
        ("ar_cuit_organization", "30-71234567-1"),
        ("ar_cuit_organization", "50-00000001-6"),
        ("au_tfn", "123 456 782"),
        ("au_tfn", TFN),
        ("gb_utr", "19558 39661"),
        ("gb_utr", UTR),
    ],
)
def test_macie_tax_formats(catalog, name: str, cell: str) -> None:
    assert _detector(catalog, name).matches(cell=cell) == [(0, len(cell))]


@pytest.mark.parametrize(
    "name, cell",
    [
        ("de_idnr", "36 574 261-809"),
        ("de_idnr", "365 742 618 09"),
        #
        # an individual's type is not an organization's, and back
        #
        ("ar_cuit_individual", "30-71234567-1"),
        ("ar_cuit_organization", "20-05536168-2"),
        ("ar_cuit_individual", "20-05536168 2"),
        ("ar_cuit_individual", "20-0553616-82"),
        #
        # an 8 digit TFN is not detected (the entry is partial)
        #
        ("au_tfn", "12345678"),
        ("au_tfn", "1123456782"),
        ("gb_utr", "1955-839661"),
        ("gb_utr", "11955839661"),
    ],
)
def test_macie_tax_not_detected(catalog, name: str, cell: str) -> None:
    assert _detector(catalog, name).matches(cell=cell) == []


# =============
# catalog entries and identifiers
# =============


def test_macie_tax_catalog(catalog) -> None:
    ind = catalog.identifier(name="ARGENTINA_INDIVIDUAL_TAX_IDENTIFICATION_NUMBER")
    org = catalog.identifier(name="ARGENTINA_ORGANIZATION_TAX_IDENTIFICATION_NUMBER")
    assert ind["keywords"] == org["keywords"]
    assert "cuit" in ind["keywords"] and "cuil" in ind["keywords"]
    #
    # Macie: organizations are MEDIUM for 1-99, HIGH from 100
    #
    assert org["severity"] == "1:MEDIUM 100:HIGH"
    assert ind["severity"] == "1:HIGH"
    de = catalog.identifier(name="GERMANY_TAX_IDENTIFICATION_NUMBER")
    au = catalog.identifier(name="AUSTRALIA_TAX_FILE_NUMBER")
    uk = catalog.identifier(name="UK_TAX_IDENTIFICATION_NUMBER")
    assert "steueridentifikationsnummer" in de["keywords"]
    assert au["keywords"] == ["tax file number", "tfn"]
    assert "utr" in uk["keywords"] and "trn" in uk["keywords"]
    assert "8 digit" in au["partial"]
    assert "TRN" in uk["partial"]
    assert "partial" not in de and "partial" not in ind and "partial" not in org
    for e in [de, ind, org, au, uk]:
        assert e["category"] == "PERSONAL_INFORMATION"
        assert e["keyword_mode"] == "required"


@pytest.mark.parametrize(
    "name, cell, header, n",
    [
        ("GERMANY_TAX_IDENTIFICATION_NUMBER", IDNR, "steuer_id", 1),
        ("GERMANY_TAX_IDENTIFICATION_NUMBER", f"Steuernummer {IDNR}", "x", 1),
        ("GERMANY_TAX_IDENTIFICATION_NUMBER", IDNR, "notes", 0),
        (
            "ARGENTINA_INDIVIDUAL_TAX_IDENTIFICATION_NUMBER",
            "cuil 20-05536168-2",
            "x",
            1,
        ),
        ("ARGENTINA_INDIVIDUAL_TAX_IDENTIFICATION_NUMBER", "30-71234567-1", "cuit", 0),
        (
            "ARGENTINA_ORGANIZATION_TAX_IDENTIFICATION_NUMBER",
            "30-71234567-1",
            "cuit",
            1,
        ),
        ("AUSTRALIA_TAX_FILE_NUMBER", "123 456 782", "tfn", 1),
        ("AUSTRALIA_TAX_FILE_NUMBER", TFN, "notes", 0),
        ("UK_TAX_IDENTIFICATION_NUMBER", f"UTR {UTR}", "x", 1),
        ("UK_TAX_IDENTIFICATION_NUMBER", UTR, "notes", 0),
    ],
)
def test_macie_tax_identifiers(
    catalog, name: str, cell: str, header: str, n: int
) -> None:
    assert (
        _mdi(catalog, name).occurrences(cell=cell, header=header, allow_lists=NO_ALLOW)
        == n
    )


@pytest.mark.parametrize(
    "name, partial",
    [
        ("GERMANY_TAX_IDENTIFICATION_NUMBER", False),
        ("ARGENTINA_ORGANIZATION_TAX_IDENTIFICATION_NUMBER", False),
        ("AUSTRALIA_TAX_FILE_NUMBER", True),
        ("UK_TAX_IDENTIFICATION_NUMBER", True),
    ],
)
def test_macie_tax_converter_reports_partial(name: str, partial: bool) -> None:
    w = MacieWrapperLoader.from_path(
        path="tests/macie/test_resources/wrappers/handcrafted_minimal.macie.json"
    )
    w["selection"]["managedDataIdentifierIds"] = [name]
    w["managedDataIdentifiers"]["resolved"] = [name]
    skipped = MacieConverter(wrapper=w).convert(name="t").report.skipped
    expected = ["managedDataIdentifier.partial"] if partial else []
    assert [s.feature for s in skipped] == expected
