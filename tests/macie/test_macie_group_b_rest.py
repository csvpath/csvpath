"""The rest of group B's shapes, the sixth group B step: Argentina DNI,
Brazil RG and CEP, Colombia cedula, Canada permanent resident (UCI), India
PAN and UK electoral roll, as FormatDetector formats. Macie publishes only
their keywords, so the formats are ours."""

import pytest

from csvpath.macie.allow_list_set import AllowListSet
from csvpath.macie.detectors.format_detector import FormatDetector
from csvpath.macie.managed_catalog import ManagedCatalog
from csvpath.macie.managed_identifier import ManagedIdentifier
from csvpath.macie.severity_levels import SeverityLevels

NO_ALLOW = AllowListSet()
#
# Macie identifier -> catalog detector
#
IDENTIFIERS = {
    "ARGENTINA_DNI_NUMBER": "ar_dni",
    "BRAZIL_RG_NUMBER": "br_rg",
    "BRAZIL_CEP_CODE": "br_cep",
    "COLOMBIA_CITIZENSHIP_CARD_NUMBER": "co_cedula",
    "CANADA_NATIONAL_IDENTIFICATION_NUMBER": "ca_pr",
    "INDIA_PERMANENT_ACCOUNT_NUMBER": "in_pan",
    "UK_ELECTORAL_ROLL_NUMBER": "gb_electoral",
}


@pytest.fixture(scope="module")
def catalog() -> ManagedCatalog:
    return ManagedCatalog.load()


def _detector(catalog, name: str) -> FormatDetector:
    return FormatDetector(config=catalog.detector(name=name))


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
    "name, cell",
    [
        ("ar_dni", "12345678"),
        ("ar_dni", "1234567"),
        ("ar_dni", "12.345.678"),
        ("ar_dni", "1.234.567"),
        ("br_rg", "12.345.678-9"),
        ("br_rg", "12.345.678-X"),
        ("br_rg", "12345678-x"),
        ("br_rg", "123456789"),
        ("br_cep", "01310-100"),
        ("br_cep", "01310100"),
        ("br_cep", "01.310-100"),
        ("co_cedula", "123456"),
        ("co_cedula", "1234567890"),
        ("co_cedula", "12.345.678"),
        ("co_cedula", "1.234.567.890"),
        ("ca_pr", "12345678"),
        ("ca_pr", "1234-5678"),
        ("ca_pr", "1234567890"),
        ("ca_pr", "12-3456-7890"),
        ("in_pan", "ABCPE1234F"),
        ("in_pan", "abcpe1234f"),
        ("gb_electoral", "AB1"),
        ("gb_electoral", "AB1234"),
    ],
)
def test_macie_group_b_rest_formats(catalog, name: str, cell: str) -> None:
    assert _detector(catalog, name).matches(cell=cell) == [(0, len(cell))]


@pytest.mark.parametrize(
    "name, cell",
    [
        #
        # too long or short; Macie's DNI exclusions, with or without dots;
        # an RG check character other than a digit or X; a PAN holder type
        # that is not issued (D); a CEP split in the wrong place
        #
        ("ar_dni", "123456789"),
        ("ar_dni", "99.999.999"),
        ("ar_dni", "99999999"),
        ("ar_dni", "00.000.000"),
        ("ar_dni", "0000000"),
        ("br_rg", "12.345.678-Y"),
        ("br_rg", "1234567890"),
        ("br_cep", "0131-0100"),
        ("co_cedula", "12345"),
        ("ca_pr", "123456789"),
        ("in_pan", "ABCDE1234F"),
        ("in_pan", "ABCP1234F"),
        ("gb_electoral", "AB12345"),
        ("gb_electoral", "ABC123"),
        ("gb_electoral", "A1234"),
    ],
)
def test_macie_group_b_rest_not_detected(catalog, name: str, cell: str) -> None:
    assert _detector(catalog, name).matches(cell=cell) == []


def test_macie_group_b_rest_catalog(catalog) -> None:
    for name, detector in IDENTIFIERS.items():
        e = catalog.identifier(name=name)
        assert e["detector"] == detector
        assert e["category"] == "PERSONAL_INFORMATION"
        assert e["keyword_mode"] == "required"
        #
        # Macie: a CEP is a mailing address, LOW for one, MEDIUM from 2,
        # HIGH from 100; national, permanent residence, taxpayer and
        # electoral roll numbers are HIGH from one
        #
        if name == "BRAZIL_CEP_CODE":
            assert e["severity"] == "1:LOW 2:MEDIUM 100:HIGH"
        else:
            assert e["severity"] == "1:HIGH"
    assert catalog.identifier(name="BRAZIL_RG_NUMBER")["keywords"] == [
        "registro geral",
        "rg",
    ]
    assert (
        "pr number"
        in (
            catalog.identifier(name="CANADA_NATIONAL_IDENTIFICATION_NUMBER")["keywords"]
        )
    )


@pytest.mark.parametrize(
    "name, cell, header, n",
    [
        ("ARGENTINA_DNI_NUMBER", "DNI 12.345.678", "x", 1),
        ("ARGENTINA_DNI_NUMBER", "12.345.678", "notes", 0),
        ("ARGENTINA_DNI_NUMBER", "dni 99.999.999", "x", 0),
        #
        # Macie says it might report an Argentine DNI as Spain's; ours does
        # not, as Spain's DNI needs its check letter
        #
        ("SPAIN_DNI_NUMBER", "DNI 12.345.678", "x", 0),
        ("BRAZIL_RG_NUMBER", "RG 12.345.678-9", "x", 1),
        ("BRAZIL_RG_NUMBER", "12.345.678-9", "registro_geral", 1),
        ("BRAZIL_CEP_CODE", "01310-100", "cep", 1),
        ("BRAZIL_CEP_CODE", "código postal 01310-100", "x", 1),
        ("BRAZIL_CEP_CODE", "01310-100", "notes", 0),
        (
            "COLOMBIA_CITIZENSHIP_CARD_NUMBER",
            "cédula de ciudadanía 1.234.567.890",
            "x",
            1,
        ),
        #
        # keywords are matched as Macie lists them: without its accents
        # this is not Colombia's keyword
        #
        (
            "COLOMBIA_CITIZENSHIP_CARD_NUMBER",
            "cedula de ciudadania 1.234.567.890",
            "x",
            0,
        ),
        ("CANADA_NATIONAL_IDENTIFICATION_NUMBER", "PR number 1234-5678", "x", 1),
        ("CANADA_NATIONAL_IDENTIFICATION_NUMBER", "1234-5678", "notes", 0),
        ("INDIA_PERMANENT_ACCOUNT_NUMBER", "PAN card ABCPE1234F", "x", 1),
        ("INDIA_PERMANENT_ACCOUNT_NUMBER", "ABCPE1234F", "pan_number", 1),
        ("UK_ELECTORAL_ROLL_NUMBER", "electoral roll number AB123", "x", 1),
        ("UK_ELECTORAL_ROLL_NUMBER", "AB123", "notes", 0),
    ],
)
def test_macie_group_b_rest_identifiers(
    catalog, name: str, cell: str, header: str, n: int
) -> None:
    assert (
        _mdi(catalog, name).occurrences(cell=cell, header=header, allow_lists=NO_ALLOW)
        == n
    )


@pytest.mark.parametrize(
    "name, cell, header",
    [
        #
        # the short keywords rg and cep match as substrings, as all
        # keywords do (transpile-design.md, fidelity item 3)
        #
        ("BRAZIL_RG_NUMBER", "org 12.345.678-9", "x"),
        ("BRAZIL_RG_NUMBER", "12.345.678-9", "cargo"),
        ("BRAZIL_CEP_CODE", "receptor 01310-100", "x"),
    ],
)
def test_macie_group_b_rest_short_keywords(
    catalog, name: str, cell: str, header: str
) -> None:
    assert (
        _mdi(catalog, name).occurrences(cell=cell, header=header, allow_lists=NO_ALLOW)
        == 1
    )
