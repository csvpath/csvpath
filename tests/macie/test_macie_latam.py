"""Brazil CPF and CNPJ, Chile RUT and Argentina SUBE stand-ins: the
checks, GroupedDigitsDetector's printed formats and prefixes, ClRutDetector,
and the catalog entries. Example numbers were checked outside
ChecksumUtility."""

import pytest

from csvpath.macie.allow_list_set import AllowListSet
from csvpath.macie.checksum_utility import ChecksumUtility as chut
from csvpath.macie.detectors.cl_rut_detector import ClRutDetector
from csvpath.macie.detectors.grouped_digits_detector import GroupedDigitsDetector
from csvpath.macie.macie_converter import MacieConverter
from csvpath.macie.macie_exceptions import MacieException
from csvpath.macie.macie_wrapper_loader import MacieWrapperLoader
from csvpath.macie.managed_catalog import ManagedCatalog
from csvpath.macie.managed_identifier import ManagedIdentifier
from csvpath.macie.severity_levels import SeverityLevels

NO_ALLOW = AllowListSet()
CPF = "52998224725"
CNPJ = "11222333000181"
SUBE = "6061123456789018"


@pytest.fixture(scope="module")
def catalog() -> ManagedCatalog:
    return ManagedCatalog.load()


def _detector(catalog, name: str) -> GroupedDigitsDetector:
    return GroupedDigitsDetector(config=catalog.detector(name=name))


@pytest.fixture(scope="module")
def rut(catalog) -> ClRutDetector:
    return ClRutDetector(config=catalog.detector(name="cl_rut"))


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
    "n, ok", [(CPF, True), ("11144477735", True), ("52998224724", False)]
)
def test_macie_cpf_mod11(n: str, ok: bool) -> None:
    assert chut.cpf_mod11(digits=n) is ok


@pytest.mark.parametrize(
    "n, ok", [(CNPJ, True), ("04252011000110", True), ("11222333000180", False)]
)
def test_macie_cnpj_mod11(n: str, ok: bool) -> None:
    assert chut.cnpj_mod11(digits=n) is ok


@pytest.mark.parametrize(
    "body, check",
    [("12345678", "5"), ("7654321", "6"), ("30686957", "4"), ("10000013", "K")],
)
def test_macie_rut_check(body: str, check: str) -> None:
    assert chut.rut_check(body=body) == check


def test_macie_latam_checks_bad_input() -> None:
    with pytest.raises(ValueError):
        chut.cpf_mod11(digits="5299822472")
    with pytest.raises(ValueError):
        chut.cnpj_mod11(digits="1122233300018a")
    with pytest.raises(ValueError):
        chut.rut_check(body="12.345")
    with pytest.raises(TypeError):
        chut.rut_check(body=None)


# =============
# CPF and CNPJ
# =============


@pytest.mark.parametrize("cell", ["529.982.247-25", CPF])
def test_macie_cpf_formats(catalog, cell: str) -> None:
    assert _detector(catalog, "br_cpf").matches(cell=cell) == [(0, len(cell))]


@pytest.mark.parametrize(
    "cell",
    [
        "529.982.247-24",
        "111.111.111-11",
        "11111111111",
        "529-982-247-25",
        "529.982.247.25",
        "1529.982.247-25",
    ],
)
def test_macie_cpf_not_a_cpf(catalog, cell: str) -> None:
    #
    # 111.111.111-11 passes the check digits but is never issued
    #
    assert _detector(catalog, "br_cpf").matches(cell=cell) == []


@pytest.mark.parametrize("cell", ["11.222.333/0001-81", CNPJ])
def test_macie_cnpj_formats(catalog, cell: str) -> None:
    assert _detector(catalog, "br_cnpj").matches(cell=cell) == [(0, len(cell))]


@pytest.mark.parametrize(
    "cell", ["11.222.333/0001-80", "00.000.000/0000-00", "11.222.333-0001-81"]
)
def test_macie_cnpj_not_a_cnpj(catalog, cell: str) -> None:
    assert _detector(catalog, "br_cnpj").matches(cell=cell) == []


def test_macie_cpf_inside_a_cnpj_is_not_a_cpf(catalog) -> None:
    #
    # 14 contiguous digits never hold an 11-digit CPF: digits must not
    # touch other digits
    #
    assert _detector(catalog, "br_cpf").matches(cell=CNPJ) == []


# =============
# SUBE
# =============


@pytest.mark.parametrize("cell", [SUBE, "6061 1234 5678 9018", "6061-1234-5678-9018"])
def test_macie_sube_formats(catalog, cell: str) -> None:
    assert _detector(catalog, "ar_sube").matches(cell=cell) == [(0, len(cell))]


def test_macie_sube_needs_its_prefix_and_luhn(catalog) -> None:
    sube = _detector(catalog, "ar_sube")
    #
    # a Luhn-valid Visa number, not 6061
    #
    assert sube.matches(cell="4532777777777774") == []
    assert sube.matches(cell="6061123456789019") == []


# =============
# GroupedDigitsDetector formats and prefixes
# =============


def test_macie_grouped_formats_and_prefixes_bad_config() -> None:
    good = {"length": 11, "formats": ["###.###.###-##"], "check": "cpf_mod11"}
    GroupedDigitsDetector(config=good)
    for bad in [
        {**good, "formats": ["###.###.###-#"]},
        {**good, "formats": ["#" * 11]},
        {**good, "formats": "###.###.###-##"},
        {**good, "prefixes": [6061]},
        {**good, "prefixes": "6061"},
    ]:
        with pytest.raises(MacieException):
            GroupedDigitsDetector(config=bad)


# =============
# RUT
# =============


@pytest.mark.parametrize(
    "cell",
    [
        "12.345.678-5",
        "12345678-5",
        "123456785",
        "7.654.321-6",
        "10.000.013-K",
        "10000013-k",
    ],
)
def test_macie_rut_formats(rut, cell: str) -> None:
    assert rut.matches(cell=cell) == [(0, len(cell))]


@pytest.mark.parametrize(
    "cell",
    [
        "12.345.678-4",
        "00.000.000-0",
        "00000000-K",
        "123.456.78-5",
        "12.345.678-",
        "x12.345.678-5",
        "12.345.678-5a",
    ],
)
def test_macie_rut_not_a_rut(rut, cell: str) -> None:
    #
    # 00.000.000-0 passes mod 11; Macie never reports all-zero numbers
    #
    assert rut.matches(cell=cell) == []


def test_macie_rut_in_text(rut) -> None:
    assert rut.matches(cell="RUT: 12.345.678-5, fono 2") == [(5, 17)]


# =============
# catalog entries and identifiers
# =============


def test_macie_latam_catalog(catalog) -> None:
    cpf = catalog.identifier(name="BRAZIL_CPF_NUMBER")
    cnpj = catalog.identifier(name="BRAZIL_CNPJ_NUMBER")
    assert cpf["keywords"] == cnpj["keywords"]
    assert "cpf" in cpf["keywords"] and "cnpj" in cpf["keywords"]
    assert "alphanumeric" in cnpj["partial"]
    assert catalog.identifier(name="CHILE_RUT_NUMBER")["severity"] == "1:HIGH"
    sube = catalog.identifier(name="ARGENTINA_TARJETA_SUBE")
    assert sube["keywords"] == ["sistema único de boleto electrónico", "sube"]
    #
    # Macie: Medium for 1-99 occurrences, High for 100 or more
    #
    assert sube["severity"] == "1:MEDIUM 100:HIGH"
    for n in [
        "BRAZIL_CPF_NUMBER",
        "BRAZIL_CNPJ_NUMBER",
        "CHILE_RUT_NUMBER",
        "ARGENTINA_TARJETA_SUBE",
    ]:
        e = catalog.identifier(name=n)
        assert e["category"] == "PERSONAL_INFORMATION"
        assert e["keyword_mode"] == "required"


def test_macie_latam_identifiers(catalog) -> None:
    assert (
        _mdi(catalog, "BRAZIL_CPF_NUMBER").occurrences(
            cell="CPF 529.982.247-25", header="x", allow_lists=NO_ALLOW
        )
        == 1
    )
    assert (
        _mdi(catalog, "CHILE_RUT_NUMBER").occurrences(
            cell="12.345.678-5", header="rut", allow_lists=NO_ALLOW
        )
        == 1
    )
    assert (
        _mdi(catalog, "ARGENTINA_TARJETA_SUBE").occurrences(
            cell=SUBE, header="notes", allow_lists=NO_ALLOW
        )
        == 0
    )


def test_macie_cnpj_converter_reports_partial() -> None:
    w = MacieWrapperLoader.from_path(
        path="tests/macie/test_resources/wrappers/handcrafted_minimal.macie.json"
    )
    w["selection"]["managedDataIdentifierIds"] = ["BRAZIL_CNPJ_NUMBER"]
    w["managedDataIdentifiers"]["resolved"] = ["BRAZIL_CNPJ_NUMBER"]
    skipped = MacieConverter(wrapper=w).convert(name="t").report.skipped
    assert [s.feature for s in skipped] == ["managedDataIdentifier.partial"]
