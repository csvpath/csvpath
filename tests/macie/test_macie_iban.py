"""IBAN stand-ins: the mod-97 check, the parameterized iban detector, the
52 country identifiers, and the partial translation of the five that also
detect BBANs in Macie. The example IBANs are the standard published ones,
checked outside ChecksumUtility."""

import pytest

from csvpath.macie.allow_list_set import AllowListSet
from csvpath.macie.checksum_utility import ChecksumUtility as chut
from csvpath.macie.detectors.iban_detector import IbanDetector
from csvpath.macie.macie_converter import MacieConverter
from csvpath.macie.macie_exceptions import MacieException
from csvpath.macie.macie_wrapper_loader import MacieWrapperLoader
from csvpath.macie.managed_catalog import ManagedCatalog
from csvpath.macie.managed_identifier import ManagedIdentifier
from csvpath.macie.severity_levels import SeverityLevels

GB = "GB29NWBK60161331926819"
DE = "DE89370400440532013000"
NL = "NL91ABNA0417164300"
FR = "FR1420041010050500013M02606"
ES = "ES9121000418450200051332"
IT = "IT60X0542811101000000123456"
CH = "CH9300762011623852957"
NO_ALLOW = AllowListSet()


@pytest.fixture(scope="module")
def catalog() -> ManagedCatalog:
    return ManagedCatalog.load()


def _detector(catalog, country: str) -> IbanDetector:
    return IbanDetector(config=catalog.detector(name="iban"), parameter=country)


# =============
# mod 97
# =============


@pytest.mark.parametrize("iban", [GB, DE, NL, FR, ES, IT, CH, GB.lower()])
def test_macie_iban_mod97_valid(iban: str) -> None:
    assert chut.iban_mod97(iban=iban) is True


@pytest.mark.parametrize(
    "iban", ["GB28NWBK60161331926819", DE[:-1] + "1", NL[:-1] + "1"]
)
def test_macie_iban_mod97_invalid(iban: str) -> None:
    assert chut.iban_mod97(iban=iban) is False


@pytest.mark.parametrize("bad", ["", "GB29", "GB29 NWBK", "GB29-NWBK", "ÄB29NWBK"])
def test_macie_iban_mod97_bad_input(bad: str) -> None:
    with pytest.raises(ValueError):
        chut.iban_mod97(iban=bad)
    with pytest.raises(TypeError):
        chut.iban_mod97(iban=None)


# =============
# detector
# =============


@pytest.mark.parametrize(
    "country, iban",
    [
        ("GB", GB),
        ("DE", DE),
        ("NL", NL),
        ("FR", FR),
        ("ES", ES),
        ("IT", IT),
        ("CH", CH),
    ],
)
def test_macie_iban_each_country(catalog, country: str, iban: str) -> None:
    assert _detector(catalog, country).matches(cell=iban) == [(0, len(iban))]


@pytest.mark.parametrize(
    "cell",
    [
        "GB29 NWBK 6016 1331 9268 19",
        "GB29-NWBK-6016-1331-9268-19",
        "gb29nwbk60161331926819",
    ],
)
def test_macie_iban_printed_layouts(catalog, cell: str) -> None:
    assert _detector(catalog, "GB").matches(cell=cell) == [(0, len(cell))]


def test_macie_iban_layout_with_full_last_group(catalog) -> None:
    #
    # ES has 24 characters: 20 after "ES91", so the last group is 4
    #
    cell = "ES91 2100 0418 4502 0005 1332"
    assert _detector(catalog, "ES").matches(cell=cell) == [(0, len(cell))]


@pytest.mark.parametrize(
    "cell",
    [
        "GB28NWBK60161331926819",
        "GB29NWBK6016133192681",
        "GB29NWBK601613319268190",
        "GB29 NWBK-6016 1331 9268 19",
        "GB29  NWBK 6016 1331 9268 19",
        "GB29 NWB K601 6133 1926 819",
        "XGB29NWBK60161331926819",
    ],
)
def test_macie_iban_not_an_iban(catalog, cell: str) -> None:
    assert _detector(catalog, "GB").matches(cell=cell) == []


def test_macie_iban_only_its_country(catalog) -> None:
    assert _detector(catalog, "DE").matches(cell=GB) == []
    assert _detector(catalog, "GB").matches(cell=f"{DE} and {GB}") == [(27, 49)]


def test_macie_iban_in_text(catalog) -> None:
    cell = f"pay to {GB}, ref 12"
    assert _detector(catalog, "GB").matches(cell=cell) == [(7, 29)]


def test_macie_iban_bad_config(catalog) -> None:
    config = catalog.detector(name="iban")
    with pytest.raises(MacieException):
        IbanDetector(config=config, parameter="ZZ")
    with pytest.raises(MacieException):
        IbanDetector(config=config, parameter=None)
    with pytest.raises(MacieException):
        IbanDetector(config={"lengths": {}}, parameter="GB")
    with pytest.raises(MacieException):
        IbanDetector(config={"lengths": {"GB": 40}}, parameter="GB")
    with pytest.raises(TypeError):
        IbanDetector(config=None, parameter="GB")


# =============
# catalog entries and identifiers
# =============


def test_macie_iban_catalog_entries(catalog) -> None:
    lengths = catalog.detector(name="iban")["lengths"]
    assert len(lengths) == 52
    #
    # these five also detect BBANs, with a keyword: the bank detector
    #
    bank = {"FRANCE": "FR", "GERMANY": "DE", "ITALY": "IT", "SPAIN": "ES", "UK": "GB"}
    for name in catalog.names:
        if not name.endswith("_BANK_ACCOUNT_NUMBER"):
            continue
        e = catalog.identifier(name=name)
        assert e["category"] == "FINANCIAL_INFORMATION"
        assert e["severity"] == "1:HIGH"
        assert e.get("partial") is None
        detector, country = ManagedCatalog.detector_parts(detector=e["detector"])
        assert country in lengths
        prefix = name[: -len("_BANK_ACCOUNT_NUMBER")]
        if prefix in bank:
            assert e["detector"] == f"bank:{bank[prefix]}"
            assert e["keyword_mode"] == "required"
            assert "account number" in e["keywords"]
        else:
            assert detector == "iban"
            assert e["keyword_mode"] == "none"
            assert e["keywords"] == []


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


def test_macie_iban_identifier_needs_no_keyword(catalog) -> None:
    uk = _mdi(catalog, "UK_BANK_ACCOUNT_NUMBER")
    assert uk.occurrences(cell=GB, header="notes", allow_lists=NO_ALLOW) == 1
    assert uk.occurrences(cell=DE, header="notes", allow_lists=NO_ALLOW) == 0


def test_macie_detector_parameter_rules(catalog) -> None:
    args = {
        "name": "X",
        "category": "FINANCIAL_INFORMATION",
        "keyword_mode": "none",
        "keywords": [],
        "distance": 30,
        "severity": SeverityLevels.parse(text="1:HIGH"),
        "catalog": catalog,
    }
    #
    # iban needs a country; credit_card takes none
    #
    with pytest.raises(MacieException):
        ManagedIdentifier(detector="iban", **args)
    with pytest.raises(MacieException):
        ManagedIdentifier(detector="credit_card:GB", **args)
    with pytest.raises(MacieException):
        ManagedIdentifier(detector="iban:", **args)


def test_macie_catalog_keywords_from_must_be_set_unless_mode_none(tmp_path) -> None:
    import json

    with open(ManagedCatalog.DEFAULT, encoding="utf-8") as f:
        c = json.load(f)
    c["identifiers"]["CREDIT_CARD_NUMBER"]["keywords_from"] = None
    p = tmp_path / "c.json"
    p.write_text(json.dumps(c), encoding="utf-8")
    with pytest.raises(MacieException):
        ManagedCatalog.load(path=str(p))


# =============
# converter
# =============


def test_macie_iban_converter_bank_and_iban_detectors() -> None:
    w = MacieWrapperLoader.from_path(
        path="tests/macie/test_resources/wrappers/handcrafted_minimal.macie.json"
    )
    ids = ["UK_BANK_ACCOUNT_NUMBER", "NETHERLANDS_BANK_ACCOUNT_NUMBER"]
    w["selection"]["managedDataIdentifierIds"] = ids
    w["managedDataIdentifiers"]["resolved"] = ids
    conversion = MacieConverter(wrapper=w).convert(name="t")
    assert '        "bank:GB",\n        "required",\n        "account code|' in (
        conversion.csvpath
    )
    assert '        "iban:NL",\n        "none",\n        "",\n' in conversion.csvpath
    #
    # nothing is partial any more: BBANs are translated
    #
    assert conversion.report.skipped == []
