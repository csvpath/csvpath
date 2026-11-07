"""Spain NIF and CIF, Mexico RFC, Colombia NIT and France TIN (SPI)
stand-ins: the checks, the detectors' forms, and the catalog entries.
test_macie_checksum_oracle compares the checks with python-stdnum on
random inputs; the published examples here are stdnum's."""

import pytest

from csvpath.macie.allow_list_set import AllowListSet
from csvpath.macie.util.checksum_utility import ChecksumUtility as chut
from csvpath.macie.detectors.co_nit_detector import CoNitDetector
from csvpath.macie.detectors.es_id_detector import EsIdDetector
from csvpath.macie.detectors.grouped_digits_detector import GroupedDigitsDetector
from csvpath.macie.detectors.mx_rfc_detector import MxRfcDetector
from csvpath.macie.macie_exceptions import MacieException
from csvpath.macie.managed_catalog import ManagedCatalog
from csvpath.macie.managed_identifier import ManagedIdentifier
from csvpath.macie.severity_levels import SeverityLevels

NO_ALLOW = AllowListSet()
CIF = "B64717838"
RFC = "GODE561231GR8"
RFC_ORG = "MAB9307148T4"
NIT_ORG = "900123456-8"
NIT = "79.123.456-0"
SPI = "3023217600053"


@pytest.fixture(scope="module")
def catalog() -> ManagedCatalog:
    return ManagedCatalog.load()


def _detector(catalog, name: str):
    if name.startswith("es_"):
        return EsIdDetector(config=catalog.detector(name=name))
    if name.startswith("mx_rfc"):
        return MxRfcDetector(config=catalog.detector(name=name))
    if name.startswith("co_nit"):
        return CoNitDetector(config=catalog.detector(name=name))
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
    "cif, ok",
    [
        (CIF, True),
        ("J99216582", True),
        ("B64717839", False),
        #
        # either the control digit or its letter, JABCDEFGHI[digit]
        #
        ("B6471783H", True),
        ("A13585625", True),
        ("A1358562E", True),
        ("A1358562F", False),
        ("q2826000h", True),
    ],
)
def test_macie_es_cif(cif: str, ok: bool) -> None:
    assert chut.es_cif(cif=cif) is ok


@pytest.mark.parametrize(
    "digits, ok",
    [
        ("2131234321", True),
        ("2131234325", False),
        ("9001234568", True),
        ("791234560", True),
        ("10123456789", True),
    ],
)
def test_macie_co_nit(digits: str, ok: bool) -> None:
    assert chut.co_nit(digits=digits) is ok


@pytest.mark.parametrize(
    "digits, ok",
    [(SPI, True), ("3023217600054", False), ("9701987765432", False)],
)
def test_macie_fr_spi(digits: str, ok: bool) -> None:
    #
    # 9701987765432 has the right mod 511 digits, but SPIs start 0 to 3
    #
    assert chut.fr_spi(digits=digits) is ok


def test_macie_tax_checks_2_bad_input() -> None:
    for bad in ["B6471783", "B647178381", "I64717838", "B6471a838"]:
        with pytest.raises(ValueError):
            chut.es_cif(cif=bad)
    with pytest.raises(TypeError):
        chut.es_cif(cif=None)
    for bad in ["1", "12345678901234567", "12a4"]:
        with pytest.raises(ValueError):
            chut.co_nit(digits=bad)
    with pytest.raises(ValueError):
        chut.fr_spi(digits="302321760005")
    assert "fr_spi" in chut.CHECKS


# =============
# Spain NIF and CIF
# =============


@pytest.mark.parametrize(
    "name, cell",
    [
        ("es_nif", "12345678Z"),
        ("es_nif", "12.345.678-Z"),
        ("es_nif", "M1234567L"),
        ("es_nif", "K-1234567-L"),
        ("es_nif", "l1234567l"),
        ("es_cif", CIF),
        ("es_cif", "B-6471783-8"),
        ("es_cif", "B6471783H"),
        ("es_cif", "J99216582"),
    ],
)
def test_macie_es_nif_cif_formats(catalog, name: str, cell: str) -> None:
    assert _detector(catalog, name).matches(cell=cell) == [(0, len(cell))]


@pytest.mark.parametrize(
    "name, cell",
    [
        #
        # a NIE is the nie form's, not the nif's: no double count
        #
        ("es_nif", "X1234567L"),
        ("es_nif", "M1234567A"),
        ("es_nif", "99999999R"),
        ("es_nif", "00000000T"),
        ("es_cif", "B64717839"),
        #
        # I, K, L, M, O, T, X, Y and Z are not CIF types
        #
        ("es_cif", "K12345670"),
        ("es_cif", "B0000000J"),
        ("es_cif", "XB64717838"),
    ],
)
def test_macie_es_nif_cif_not_detected(catalog, name: str, cell: str) -> None:
    assert _detector(catalog, name).matches(cell=cell) == []


# =============
# Mexico RFC
# =============


@pytest.mark.parametrize(
    "name, cell",
    [
        ("mx_rfc_individual", RFC),
        ("mx_rfc_individual", "GODE 561231 GR8"),
        ("mx_rfc_individual", "GODE-561231-GR8"),
        #
        # a wrong check digit is not checked (David, 2026-11-03)
        #
        ("mx_rfc_individual", "VACE460910SX6"),
        ("mx_rfc_individual", "MUÑO800229AB1"),
        ("mx_rfc_individual", "gode561231gr8"),
        ("mx_rfc_organization", RFC_ORG),
        ("mx_rfc_organization", "MAB-930714-8T4"),
        ("mx_rfc_organization", "A&B000229XY1"),
    ],
)
def test_macie_rfc_formats(catalog, name: str, cell: str) -> None:
    assert _detector(catalog, name).matches(cell=cell) == [(0, len(cell))]


@pytest.mark.parametrize(
    "name, cell",
    [
        ("mx_rfc_individual", "GODE561331GR8"),
        ("mx_rfc_individual", "GODE561231-GR8"),
        ("mx_rfc_individual", "GODE561231GR"),
        #
        # Macie's examples
        #
        ("mx_rfc_individual", "XAXX010101000"),
        ("mx_rfc_individual", "XEXX010101000"),
        #
        # an individual's RFC is not an organization's, and back
        #
        ("mx_rfc_organization", RFC),
        ("mx_rfc_individual", RFC_ORG),
        ("mx_rfc_organization", "MAB930230AB1"),
    ],
)
def test_macie_rfc_not_detected(catalog, name: str, cell: str) -> None:
    assert _detector(catalog, name).matches(cell=cell) == []


# =============
# Colombia NIT
# =============


@pytest.mark.parametrize(
    "name, cell",
    [
        ("co_nit_organization", NIT_ORG),
        ("co_nit_organization", "900.123.456-8"),
        ("co_nit_organization", "9001234568"),
        ("co_nit_organization", "860000123-8"),
        ("co_nit_individual", NIT),
        ("co_nit_individual", "79123456-0"),
        ("co_nit_individual", "1.012.345.678-9"),
        #
        # 9 digits not starting 8 or 9: a person's
        #
        ("co_nit_individual", "101234567-5"),
        ("co_nit_individual", "213.123.432-1"),
    ],
)
def test_macie_nit_formats(catalog, name: str, cell: str) -> None:
    assert _detector(catalog, name).matches(cell=cell) == [(0, len(cell))]


@pytest.mark.parametrize(
    "name, cell",
    [
        ("co_nit_organization", "900.123.456-7"),
        ("co_nit_individual", NIT_ORG),
        ("co_nit_organization", NIT),
        ("co_nit_individual", "000000000-0"),
        ("co_nit_individual", "12345-5"),
        ("co_nit_individual", "90.0123.456-8"),
        ("co_nit_organization", "1900123456-8"),
    ],
)
def test_macie_nit_not_detected(catalog, name: str, cell: str) -> None:
    assert _detector(catalog, name).matches(cell=cell) == []


def test_macie_nit_in_text(catalog) -> None:
    d = _detector(catalog, "co_nit_organization")
    assert d.matches(cell="NIT 900.123.456-8.") == [(4, 17)]


# =============
# France TIN
# =============


@pytest.mark.parametrize("cell", [SPI, "30 23 217 600 053", "30-23-217-600-053"])
def test_macie_spi_formats(catalog, cell: str) -> None:
    assert _detector(catalog, "fr_spi").matches(cell=cell) == [(0, len(cell))]


@pytest.mark.parametrize(
    "cell", ["3023217600054", "9701987765432", "302 321 760 0053", "30232176000531"]
)
def test_macie_spi_not_detected(catalog, cell: str) -> None:
    assert _detector(catalog, "fr_spi").matches(cell=cell) == []


def test_macie_tax_detectors_2_bad_config() -> None:
    for cls in [MxRfcDetector, CoNitDetector]:
        with pytest.raises(TypeError):
            cls(config=None)
        for bad in [{}, {"form": "person"}]:
            with pytest.raises(MacieException):
                cls(config=bad)
        with pytest.raises(TypeError):
            cls(config={"form": "individual"}).matches(cell=None)


# =============
# catalog entries and identifiers
# =============


def test_macie_tax_catalog_2(catalog) -> None:
    names = [
        "SPAIN_NIF_NUMBER",
        "SPAIN_TAX_IDENTIFICATION_NUMBER",
        "MEXICO_INDIVIDUAL_RFC_NUMBER",
        "MEXICO_ORGANIZATION_RFC_NUMBER",
        "COLOMBIA_INDIVIDUAL_NIT_NUMBER",
        "COLOMBIA_ORGANIZATION_NIT_NUMBER",
        "FRANCE_TAX_IDENTIFICATION_NUMBER",
    ]
    e = {n: catalog.identifier(name=n) for n in names}
    #
    # Spain's NIE, NIF and CIF share Spain's taxpayer keywords
    #
    nie = catalog.identifier(name="SPAIN_NIE_NUMBER")
    assert e["SPAIN_NIF_NUMBER"]["keywords"] == nie["keywords"]
    assert e["SPAIN_TAX_IDENTIFICATION_NUMBER"]["keywords"] == nie["keywords"]
    assert "rfc" in e["MEXICO_INDIVIDUAL_RFC_NUMBER"]["keywords"]
    assert e["COLOMBIA_INDIVIDUAL_NIT_NUMBER"]["keywords"] == [
        "nit",
        "nit.",
        "nit#",
        "n.i.t.",
    ]
    assert "tin" in e["FRANCE_TAX_IDENTIFICATION_NUMBER"]["keywords"]
    for n in names:
        assert e[n]["category"] == "PERSONAL_INFORMATION"
        assert e[n]["keyword_mode"] == "required"
        assert "partial" not in e[n]
        expected = "1:MEDIUM 100:HIGH" if "ORGANIZATION" in n else "1:HIGH"
        assert e[n]["severity"] == expected


@pytest.mark.parametrize(
    "name, cell, header, n",
    [
        ("SPAIN_NIF_NUMBER", "NIF M1234567L", "x", 1),
        ("SPAIN_NIF_NUMBER", "X1234567L", "nif", 0),
        ("SPAIN_NIE_NUMBER", "X1234567L", "nif", 1),
        ("SPAIN_TAX_IDENTIFICATION_NUMBER", CIF, "cif", 1),
        ("SPAIN_TAX_IDENTIFICATION_NUMBER", CIF, "notes", 0),
        ("MEXICO_INDIVIDUAL_RFC_NUMBER", f"RFC {RFC}", "x", 1),
        ("MEXICO_ORGANIZATION_RFC_NUMBER", RFC_ORG, "rfc", 1),
        ("MEXICO_ORGANIZATION_RFC_NUMBER", RFC_ORG, "notes", 0),
        ("COLOMBIA_ORGANIZATION_NIT_NUMBER", f"NIT {NIT_ORG}", "x", 1),
        ("COLOMBIA_INDIVIDUAL_NIT_NUMBER", NIT, "nit", 1),
        ("COLOMBIA_INDIVIDUAL_NIT_NUMBER", NIT, "notes", 0),
        ("FRANCE_TAX_IDENTIFICATION_NUMBER", "30 23 217 600 053", "tin", 1),
        ("FRANCE_TAX_IDENTIFICATION_NUMBER", SPI, "notes", 0),
    ],
)
def test_macie_tax_identifiers_2(
    catalog, name: str, cell: str, header: str, n: int
) -> None:
    assert (
        _mdi(catalog, name).occurrences(cell=cell, header=header, allow_lists=NO_ALLOW)
        == n
    )
