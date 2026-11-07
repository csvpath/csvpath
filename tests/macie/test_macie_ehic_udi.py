"""EHIC card numbers and medical device UDIs, the last group A leftovers:
EhicDetector (the EU and Finland), UdiDetector (GS1 and HIBCC), their
checks, and the catalog entries. The GS1 check is also compared with
python-stdnum in test_macie_checksum_oracle.py."""

import pytest

from csvpath.macie.allow_list_set import AllowListSet
from csvpath.macie.util.checksum_utility import ChecksumUtility as chut
from csvpath.macie.detectors.ehic_detector import EhicDetector
from csvpath.macie.detectors.udi_detector import UdiDetector
from csvpath.macie.macie_exceptions import MacieException
from csvpath.macie.managed_catalog import ManagedCatalog
from csvpath.macie.managed_identifier import ManagedIdentifier
from csvpath.macie.severity_levels import SeverityLevels

NO_ALLOW = AllowListSet()
UDI = UdiDetector(config={})


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


@pytest.mark.parametrize(
    "cell, eu, fi",
    [
        #
        # Finland (246) is in both; Germany (276) only in the EU's
        #
        ("80246123456789012345", True, True),
        ("8024612345 6789012345", True, True),
        ("8024612345-6789012345", True, True),
        ("80246-12345-67890-12345", True, True),
        ("80276 00000 12345 67890", True, False),
        ("80826000001234567890", True, False),
        #
        # not 80 and a listed country; mixed separators; too long; touching
        # a letter
        #
        ("12345678901234567890", False, False),
        ("80999123456789012345", False, False),
        ("80840123456789012345", False, False),
        ("80246 12345-67890 12345", False, False),
        ("802461234567890123456", False, False),
        ("8024612345678901234x", False, False),
    ],
)
def test_macie_ehic_forms(catalog, cell: str, eu: bool, fi: bool) -> None:
    whole = [(0, len(cell))]
    eu_d = EhicDetector(config=catalog.detector(name="eu_ehic"))
    fi_d = EhicDetector(config=catalog.detector(name="fi_ehic"))
    assert (eu_d.matches(cell=cell) == whole) is eu
    assert (fi_d.matches(cell=cell) == whole) is fi


def test_macie_ehic_bad_config() -> None:
    with pytest.raises(TypeError):
        EhicDetector(config=None)
    for bad in [{}, {"countries": []}, {"countries": ["24"]}, {"countries": [246]}]:
        with pytest.raises(MacieException):
            EhicDetector(config=bad)
    with pytest.raises(TypeError):
        EhicDetector(config={"countries": ["246"]}).matches(cell=None)


def test_macie_gs1_and_hibcc_checks() -> None:
    #
    # GS1's documented GTIN-14, and two HIBCC specification examples
    #
    assert chut.gs1_check(digits="00614141999996") is True
    assert chut.gs1_check(digits="00614141999997") is False
    assert chut.hibcc_mod43(text="+A123BJC5D6E71") == "G"
    assert chut.hibcc_mod43(text="+H123ABC01234567890") == "D"
    with pytest.raises(ValueError):
        chut.gs1_check(digits="1")
    with pytest.raises(ValueError):
        chut.hibcc_mod43(text="+a123")
    with pytest.raises(TypeError):
        chut.hibcc_mod43(text=None)


@pytest.mark.parametrize(
    "cell",
    [
        "(01)00614141999996",
        "(01)00614141999996(17)250101(10)A1",
        "(01)00614141999996(11)240101(17)290101(10)LOT-7/B(21)SN12345",
        "+A123BJC5D6E71G",
        "+H123ABC01234567890D",
    ],
)
def test_macie_udi_forms(cell: str) -> None:
    assert UDI.matches(cell=cell) == [(0, len(cell))]


@pytest.mark.parametrize(
    "cell",
    [
        #
        # a failed GS1 or mod 43 check; a short GTIN; touching letters;
        # lower case HIBCC; no labeler code; ISBT 128 (not detected yet)
        #
        "(01)00614141999997",
        "(01)0061414199999",
        "x(01)00614141999996",
        "+A123BJC5D6E71H",
        "+a123BJC5D6E71G",
        "x+A123BJC5D6E71G",
        "+1234567",
        "=/A9999XYZ100T0944",
    ],
)
def test_macie_udi_not_detected(cell: str) -> None:
    assert UDI.matches(cell=cell) == []


def test_macie_udi_in_text() -> None:
    cell = "udi +A123BJC5D6E71G and (01)00614141999996"
    assert UDI.matches(cell=cell) == [(4, 19), (24, 42)]


def test_macie_udi_bad_input() -> None:
    with pytest.raises(TypeError):
        UdiDetector(config=None)
    with pytest.raises(TypeError):
        UDI.matches(cell=None)


def test_macie_ehic_udi_catalog(catalog) -> None:
    for name in [
        "EUROPEAN_HEALTH_INSURANCE_CARD_NUMBER",
        "FINLAND_EUROPEAN_HEALTH_INSURANCE_NUMBER",
    ]:
        e = catalog.identifier(name=name)
        assert e["category"] == "PERSONAL_INFORMATION"
        assert e["keyword_mode"] == "required"
        assert e["severity"] == "1:HIGH"
    fi = catalog.identifier(name="FINLAND_EUROPEAN_HEALTH_INSURANCE_NUMBER")
    #
    # Macie lists sairaanhoitokortin twice for Finland; once here
    #
    assert fi["keywords"].count("sairaanhoitokortin") == 1
    assert len(fi["keywords"]) == 18
    assert len(catalog.detector(name="eu_ehic")["countries"]) == 32
    udi = catalog.identifier(name="MEDICAL_DEVICE_UDI")
    #
    # Macie: UDIs are LOW for one, MEDIUM from 2, HIGH from 100
    #
    assert udi["severity"] == "1:LOW 2:MEDIUM 100:HIGH"
    assert "med" in udi["keywords"]
    #
    # Macie names ISBT 128 too; the converter reports the shortfall
    #
    assert "ISBT 128" in udi["partial"]


@pytest.mark.parametrize(
    "name, cell, header, n",
    [
        (
            "EUROPEAN_HEALTH_INSURANCE_CARD_NUMBER",
            "ehic 80276 00000 12345 67890",
            "x",
            1,
        ),
        ("EUROPEAN_HEALTH_INSURANCE_CARD_NUMBER", "80276000001234567890", "notes", 0),
        (
            "FINLAND_EUROPEAN_HEALTH_INSURANCE_NUMBER",
            "8024612345 6789012345",
            "terveyskortti",
            1,
        ),
        (
            "FINLAND_EUROPEAN_HEALTH_INSURANCE_NUMBER",
            "ehic 80276000001234567890",
            "x",
            0,
        ),
        ("MEDICAL_DEVICE_UDI", "udi (01)00614141999996", "x", 1),
        ("MEDICAL_DEVICE_UDI", "+A123BJC5D6E71G", "device_id", 1),
        ("MEDICAL_DEVICE_UDI", "(01)00614141999996", "notes", 0),
    ],
)
def test_macie_ehic_udi_identifiers(
    catalog, name: str, cell: str, header: str, n: int
) -> None:
    assert (
        _mdi(catalog, name).occurrences(cell=cell, header=header, allow_lists=NO_ALLOW)
        == n
    )


def test_macie_udi_short_keyword(catalog) -> None:
    #
    # med matches as a substring (fidelity item 3): medium, named, a
    # medication column
    #
    mdi = _mdi(catalog, "MEDICAL_DEVICE_UDI")
    assert (
        mdi.occurrences(
            cell="(01)00614141999996", header="medication", allow_lists=NO_ALLOW
        )
        == 1
    )
