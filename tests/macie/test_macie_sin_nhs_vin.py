"""Canada SIN, UK NHS number and VIN stand-ins: the NHS mod 11 check,
GroupedDigitsDetector (used by ca_sin and uk_nhs), VinDetector, and their
catalog entries. Example numbers were checked outside ChecksumUtility."""

import pytest

from csvpath.macie.allow_list_set import AllowListSet
from csvpath.macie.checksum_utility import ChecksumUtility as chut
from csvpath.macie.detectors import DETECTORS
from csvpath.macie.detectors.grouped_digits_detector import GroupedDigitsDetector
from csvpath.macie.detectors.vin_detector import VinDetector
from csvpath.macie.macie_exceptions import MacieException
from csvpath.macie.managed_catalog import ManagedCatalog
from csvpath.macie.managed_identifier import ManagedIdentifier
from csvpath.macie.severity_levels import SeverityLevels

NO_ALLOW = AllowListSet()
NA_VIN = "1HGCM82633A004352"
EU_VIN = "WVWZZZ1KZ6W612305"


@pytest.fixture(scope="module")
def catalog() -> ManagedCatalog:
    return ManagedCatalog.load()


@pytest.fixture(scope="module")
def sin(catalog) -> GroupedDigitsDetector:
    return GroupedDigitsDetector(config=catalog.detector(name="ca_sin"))


@pytest.fixture(scope="module")
def nhs(catalog) -> GroupedDigitsDetector:
    return GroupedDigitsDetector(config=catalog.detector(name="uk_nhs"))


@pytest.fixture(scope="module")
def vin(catalog) -> VinDetector:
    return VinDetector(config=catalog.detector(name="vin"))


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
# NHS mod 11
# =============


@pytest.mark.parametrize("n", ["9434765919", "4010232137"])
def test_macie_nhs_mod11_valid(n: str) -> None:
    assert chut.nhs_mod11(digits=n) is True


def test_macie_nhs_mod11_invalid() -> None:
    assert chut.nhs_mod11(digits="9434765918") is False
    #
    # weighted sum 1*10 + 1*9 + 0 ... = 19, 19 % 11 = 8, 11 - 8 = 3: so
    # 1100000003 is valid and 1100000004 is not
    #
    assert chut.nhs_mod11(digits="1100000003") is True
    assert chut.nhs_mod11(digits="1100000004") is False


def test_macie_nhs_mod11_check_of_ten_is_never_valid() -> None:
    #
    # 1000000010: 1*10 + 1*2 = 12, 12 % 11 = 1, 11 - 1 = 10: never issued
    #
    for last in "0123456789":
        assert chut.nhs_mod11(digits="100000001" + last) is False


def test_macie_checks_by_name() -> None:
    assert chut.check(name="luhn", digits="130692544") is True
    assert chut.check(name="nhs_mod11", digits="9434765919") is True
    with pytest.raises(ValueError):
        chut.check(name="mod7", digits="1")
    with pytest.raises(ValueError):
        chut.nhs_mod11(digits="943476591")


# =============
# SIN
# =============


@pytest.mark.parametrize(
    "cell", ["130 692 544", "130-692-544", "130692544", "193456787"]
)
def test_macie_sin_valid(sin, cell: str) -> None:
    assert sin.matches(cell=cell) == [(0, len(cell))]


@pytest.mark.parametrize(
    "cell",
    [
        "130 692 545",
        "046 454 286",
        "046454286",
        "130 692-544",
        "13 0692 544",
        "1130 692 544",
    ],
)
def test_macie_sin_not_a_sin(sin, cell: str) -> None:
    assert sin.matches(cell=cell) == []


def test_macie_sin_never_starts_with_0_or_8(sin) -> None:
    #
    # both pass Luhn
    #
    assert chut.luhn(digits="000000000") is True
    assert sin.matches(cell="000 000 000") == []
    assert chut.luhn(digits="800000002") is True
    assert sin.matches(cell="800 000 002") == []


# =============
# NHS
# =============


@pytest.mark.parametrize("cell", ["943 476 5919", "943-476-5919", "9434765919"])
def test_macie_nhs_valid(nhs, cell: str) -> None:
    assert nhs.matches(cell=cell) == [(0, len(cell))]


@pytest.mark.parametrize(
    "cell", ["943 476 5918", "9434 765 919", "94347659190", "943 476-5919"]
)
def test_macie_nhs_not_an_nhs_number(nhs, cell: str) -> None:
    assert nhs.matches(cell=cell) == []


def test_macie_grouped_digits_bad_config() -> None:
    good = {"length": 9, "layouts": [[3, 3, 3]], "check": "luhn"}
    GroupedDigitsDetector(config=good)
    for bad in [
        {**good, "length": 1},
        {**good, "check": "mod7"},
        {**good, "layouts": [[3, 3]]},
        {**good, "layouts": [[9]]},
        {**good, "layouts": "3-3-3"},
        {**good, "exclusions": ["12345678"]},
    ]:
        with pytest.raises(MacieException):
            GroupedDigitsDetector(config=bad)
    with pytest.raises(TypeError):
        GroupedDigitsDetector(config=None)


def test_macie_one_class_two_detectors() -> None:
    assert DETECTORS["ca_sin"] is GroupedDigitsDetector
    assert DETECTORS["uk_nhs"] is GroupedDigitsDetector


# =============
# VIN
# =============


@pytest.mark.parametrize("cell", [NA_VIN, EU_VIN])
def test_macie_vin_valid(vin, cell: str) -> None:
    assert vin.matches(cell=cell) == [(0, 17)]


def test_macie_vin_check_digit_is_not_required(vin) -> None:
    #
    # the European VIN has no North American check digit; a North American
    # one with a wrong check digit is also reported
    #
    assert vin.matches(cell=EU_VIN) == [(0, 17)]
    assert vin.matches(cell="1HGCM82633A004353") == [(0, 17)]


@pytest.mark.parametrize(
    "cell",
    [
        #
        # I, O and Q are never used
        #
        "1HGCM82I33A004352",
        "1HGCM82O33A004352",
        "1HGCM82Q33A004352",
        #
        # position 10 (the model year) is never U, Z or 0
        #
        "1HGCM8263UA004352",
        "1HGCM8263ZA004352",
        "1HGCM82630A004352",
        #
        # 16 and 18 characters, touching other characters, lower case
        #
        "1HGCM82633A00435",
        "1HGCM82633A0043521",
        "X1HGCM82633A004352",
        "1hgcm82633a004352",
        #
        # all digits or all letters
        #
        "12345678912345678",
        "ABCDEFGHJKLMNPRST",
    ],
)
def test_macie_vin_not_a_vin(vin, cell: str) -> None:
    assert vin.matches(cell=cell) == []


def test_macie_vin_in_text(vin) -> None:
    assert vin.matches(cell=f"VIN: {NA_VIN}, plate 7ABC123") == [(5, 22)]


# =============
# catalog entries
# =============


def test_macie_sin_nhs_vin_catalog(catalog) -> None:
    sin = catalog.identifier(name="CANADA_SOCIAL_INSURANCE_NUMBER")
    assert sin["keywords"] == [
        "canadian id",
        "numéro d'assurance sociale",
        "sin",
        "social insurance number",
    ]
    assert sin["severity"] == "1:HIGH"
    nhs = catalog.identifier(name="UK_NHS_NUMBER")
    assert nhs["keywords"] == ["national health service", "nhs"]
    assert nhs["severity"] == "1:HIGH"
    vin = catalog.identifier(name="VEHICLE_IDENTIFICATION_NUMBER")
    assert len(vin["keywords"]) == 11
    #
    # Macie: Low for 1-99 occurrences, Medium for 100 or more
    #
    assert vin["severity"] == "1:LOW 100:MEDIUM"
    assert vin["fidelity"] == "B"
    for e in [sin, nhs, vin]:
        assert e["category"] == "PERSONAL_INFORMATION"
        assert e["keyword_mode"] == "required"


def test_macie_sin_nhs_vin_identifiers(catalog) -> None:
    assert (
        _mdi(catalog, "CANADA_SOCIAL_INSURANCE_NUMBER").occurrences(
            cell="sin 130 692 544", header="x", allow_lists=NO_ALLOW
        )
        == 1
    )
    assert (
        _mdi(catalog, "UK_NHS_NUMBER").occurrences(
            cell="943 476 5919", header="nhs_number", allow_lists=NO_ALLOW
        )
        == 1
    )
    assert (
        _mdi(catalog, "VEHICLE_IDENTIFICATION_NUMBER").occurrences(
            cell=NA_VIN, header="notes", allow_lists=NO_ALLOW
        )
        == 0
    )
    assert (
        _mdi(catalog, "VEHICLE_IDENTIFICATION_NUMBER").occurrences(
            cell=f"numéro d'identification du véhicule {EU_VIN}",
            header="notes",
            allow_lists=NO_ALLOW,
        )
        == 1
    )
