"""BBANs: the French RIB key and Spanish check digits, BankAccountDetector
(bank:FR, bank:DE, bank:IT, bank:ES, bank:GB), and the keyword exemption
for IBANs. Example BBANs come from published IBANs that pass mod 97."""

import pytest

from csvpath.macie.allow_list_set import AllowListSet
from csvpath.macie.util.checksum_utility import ChecksumUtility as chut
from csvpath.macie.detectors.bank_account_detector import BankAccountDetector
from csvpath.macie.macie_exceptions import MacieException
from csvpath.macie.managed_catalog import ManagedCatalog
from csvpath.macie.managed_identifier import ManagedIdentifier
from csvpath.macie.severity_levels import SeverityLevels

FR = "20041010050500013M02606"
FR2 = "30006000011234567890189"
ES = "21000418450200051332"
ES2 = "21000813610123456789"
IT = "X0542811101000000123456"
DE = "370400440532013000"
GB = "NWBK60161331926819"
NO_ALLOW = AllowListSet()


@pytest.fixture(scope="module")
def catalog() -> ManagedCatalog:
    return ManagedCatalog.load()


def _bank(catalog, country: str) -> BankAccountDetector:
    return BankAccountDetector(config=catalog.detector(name="bank"), parameter=country)


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


@pytest.mark.parametrize("bban", [FR, FR2, FR.lower()])
def test_macie_fr_rib_key_valid(bban: str) -> None:
    assert chut.fr_rib_key(bban=bban) is True


def test_macie_fr_rib_key_invalid_and_bad_input() -> None:
    assert chut.fr_rib_key(bban=FR[:-1] + "7") is False
    for bad in ["", FR[:-1], "2004101005050001-M02606", "A0041010050500013M02606"]:
        with pytest.raises(ValueError):
            chut.fr_rib_key(bban=bad)
    with pytest.raises(TypeError):
        chut.fr_rib_key(bban=None)


@pytest.mark.parametrize(
    "bban, ok", [(ES, True), (ES2, True), (ES[:9] + "6" + ES[10:], False)]
)
def test_macie_es_bban(bban: str, ok: bool) -> None:
    assert chut.es_bban(bban=bban) is ok


# =============
# BBAN layouts, per country
# =============


@pytest.mark.parametrize(
    "country, cell",
    [
        ("FR", FR),
        ("FR", "2004 1010 0505 0001 3M02 606"),
        ("FR", "20041 01005 0500013M026 06"),
        ("FR", FR.lower()),
        ("ES", ES),
        ("ES", "2100 0418 4502 0005 1332"),
        ("ES", "2100 0418 45 0200051332"),
        ("IT", IT),
        ("IT", "X054 2811 1010 0000 0123 456"),
        ("IT", "X 05428 11101 000000123456"),
        ("DE", DE),
        ("DE", "3704 0044 0532 0130 00"),
        ("DE", "37040044 0532013000"),
        ("GB", GB),
        ("GB", "NWBK 6016 1331 9268 19"),
        ("GB", "NWBK 601613 31926819"),
        ("GB", "60-16-13 31926819"),
        ("GB", "60 16 13 31926819"),
    ],
)
def test_macie_bban_layouts(catalog, country: str, cell: str) -> None:
    assert _bank(catalog, country).matches(cell=cell) == [(0, len(cell))]


@pytest.mark.parametrize(
    "country, cell",
    [
        #
        # bad RIB key and bad Spanish check digits
        #
        ("FR", FR[:-1] + "7"),
        ("ES", ES[:9] + "6" + ES[10:]),
        #
        # wrong lengths and shapes
        #
        ("DE", DE[:-1]),
        ("DE", DE + "0"),
        ("GB", "NWB160161331926819"),
        ("IT", "10542811101000000123456"),
        #
        # mixed separators
        #
        ("DE", "3704 0044-0532 0130 00"),
        ("GB", "60-16 13 31926819"),
    ],
)
def test_macie_bban_not_a_bban(catalog, country: str, cell: str) -> None:
    assert _bank(catalog, country).matches(cell=cell) == []


def test_macie_bban_italian_cin_is_not_checked(catalog) -> None:
    #
    # any letter: the CIN rule is not confirmed, and a wrong rule would
    # miss real accounts
    #
    assert _bank(catalog, "IT").matches(cell="Y" + IT[1:]) == [(0, 23)]


def test_macie_bank_finds_ibans_too_without_double_counting(catalog) -> None:
    bank = _bank(catalog, "GB")
    iban = "GB29NWBK60161331926819"
    assert bank.matches(cell=iban) == [(0, 22)]
    printed = "GB29 NWBK 6016 1331 9268 19"
    #
    # the BBAN inside the printed IBAN is part of the IBAN, not a second
    # account
    #
    assert bank.matches(cell=printed) == [(0, len(printed))]
    assert bank.matches(cell=f"{iban} and {GB}") == [(0, 22), (27, 45)]


def test_macie_bank_keyword_exemption(catalog) -> None:
    bank = _bank(catalog, "GB")
    cell = f"GB29NWBK60161331926819 {GB}"
    assert bank.keyword_exempt(cell=cell, start=0, end=22) is True
    assert bank.keyword_exempt(cell=cell, start=23, end=41) is False


def test_macie_bank_bad_config(catalog) -> None:
    config = catalog.detector(name="bank")
    with pytest.raises(MacieException):
        BankAccountDetector(config=config, parameter="NL")
    with pytest.raises(MacieException):
        BankAccountDetector(config={**config, "iban_lengths": None}, parameter="GB")
    bad = {**config["bban"]["GB"], "shape": "AAAA##X"}
    with pytest.raises(MacieException):
        BankAccountDetector(config={**config, "bban": {"GB": bad}}, parameter="GB")
    bad = {**config["bban"]["GB"], "layouts": [[4, 4]]}
    with pytest.raises(MacieException):
        BankAccountDetector(config={**config, "bban": {"GB": bad}}, parameter="GB")
    bad = {**config["bban"]["GB"], "check": "mod7"}
    with pytest.raises(MacieException):
        BankAccountDetector(config={**config, "bban": {"GB": bad}}, parameter="GB")
    with pytest.raises(TypeError):
        BankAccountDetector(config=None, parameter="GB")


def test_macie_bank_iban_lengths_match_the_iban_detector(catalog) -> None:
    iban = catalog.detector(name="iban")["lengths"]
    bank = catalog.detector(name="bank")["iban_lengths"]
    assert set(bank) == {"FR", "DE", "IT", "ES", "GB"}
    assert {k: iban[k] for k in bank} == bank


# =============
# the identifiers: IBANs need no keyword, BBANs do
# =============


def test_macie_bank_identifier_keyword_rule(catalog) -> None:
    uk = _mdi(catalog, "UK_BANK_ACCOUNT_NUMBER")
    assert (
        uk.occurrences(
            cell="GB29NWBK60161331926819", header="notes", allow_lists=NO_ALLOW
        )
        == 1
    )
    assert uk.occurrences(cell=GB, header="notes", allow_lists=NO_ALLOW) == 0
    assert uk.occurrences(cell=GB, header="account_number", allow_lists=NO_ALLOW) == 1
    assert uk.occurrences(cell=f"bban {GB}", header="notes", allow_lists=NO_ALLOW) == 1
    assert (
        uk.occurrences(cell="60-16-13 31926819", header="notes", allow_lists=NO_ALLOW)
        == 0
    )
    assert (
        uk.occurrences(
            cell="account number 60-16-13 31926819",
            header="notes",
            allow_lists=NO_ALLOW,
        )
        == 1
    )


def test_macie_bank_identifier_country_keywords(catalog) -> None:
    de = _mdi(catalog, "GERMANY_BANK_ACCOUNT_NUMBER")
    assert (
        de.occurrences(cell=f"Kontonummer {DE}", header="x", allow_lists=NO_ALLOW) == 1
    )
    fr = _mdi(catalog, "FRANCE_BANK_ACCOUNT_NUMBER")
    assert (
        fr.occurrences(cell=f"compte bancaire {FR}", header="x", allow_lists=NO_ALLOW)
        == 1
    )
    #
    # a German keyword is not a French one
    #
    assert (
        fr.occurrences(cell=f"Kontonummer {FR}", header="x", allow_lists=NO_ALLOW) == 0
    )
