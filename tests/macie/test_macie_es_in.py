"""Spain DNI and NIE and India Aadhaar stand-ins: the checks, EsIdDetector,
GroupedDigitsDetector's Aadhaar data, and the catalog entries. The
Verhoeff numbers were checked outside ChecksumUtility, by the dihedral
group's arithmetic rather than its tables; 12345678Z and X1234567L are
the Ministerio del Interior's published examples."""

import pytest

from csvpath.macie.allow_list_set import AllowListSet
from csvpath.macie.util.checksum_utility import ChecksumUtility as chut
from csvpath.macie.detectors.es_id_detector import EsIdDetector
from csvpath.macie.detectors.grouped_digits_detector import GroupedDigitsDetector
from csvpath.macie.macie_exceptions import MacieException
from csvpath.macie.managed_catalog import ManagedCatalog
from csvpath.macie.managed_identifier import ManagedIdentifier
from csvpath.macie.severity_levels import SeverityLevels

NO_ALLOW = AllowListSet()
AADHAAR = "234567890124"


@pytest.fixture(scope="module")
def catalog() -> ManagedCatalog:
    return ManagedCatalog.load()


@pytest.fixture(scope="module")
def dni(catalog) -> EsIdDetector:
    return EsIdDetector(config=catalog.detector(name="es_dni"))


@pytest.fixture(scope="module")
def nie(catalog) -> EsIdDetector:
    return EsIdDetector(config=catalog.detector(name="es_nie"))


@pytest.fixture(scope="module")
def aadhaar(catalog) -> GroupedDigitsDetector:
    return GroupedDigitsDetector(config=catalog.detector(name="in_aadhaar"))


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
    "digits, ok",
    [
        #
        # Wikipedia's examples: 236 has check digit 3, 12345 has 1
        #
        ("2363", True),
        ("2364", False),
        ("123451", True),
        (AADHAAR, True),
        ("234567890125", False),
        ("987654321012", True),
        ("500000000006", True),
    ],
)
def test_macie_verhoeff(digits: str, ok: bool) -> None:
    assert chut.verhoeff(digits=digits) is ok


def test_macie_verhoeff_catches_adjacent_transpositions() -> None:
    #
    # what Verhoeff adds over Luhn: every swap of two adjacent digits
    # fails, e.g. 09 <-> 90
    #
    for i in range(len(AADHAAR) - 1):
        if AADHAAR[i] == AADHAAR[i + 1]:
            continue
        swapped = AADHAAR[:i] + AADHAAR[i + 1] + AADHAAR[i] + AADHAAR[i + 2 :]
        assert chut.verhoeff(digits=swapped) is False


@pytest.mark.parametrize(
    "number, letter",
    [
        ("12345678", "Z"),
        ("87654321", "X"),
        ("00000001", "R"),
        ("X1234567", "L"),
        ("Y1234567", "X"),
        ("Z7654321", "H"),
        ("x1234567", "L"),
    ],
)
def test_macie_es_id_letter(number: str, letter: str) -> None:
    assert chut.es_id_letter(number=number) == letter


def test_macie_es_in_checks_bad_input() -> None:
    with pytest.raises(ValueError):
        chut.verhoeff(digits="1")
    with pytest.raises(ValueError):
        chut.verhoeff(digits="12a4")
    with pytest.raises(TypeError):
        chut.verhoeff(digits=None)
    for bad in ["1234567", "123456789", "A1234567", "X123456", "12.345.678"]:
        with pytest.raises(ValueError):
            chut.es_id_letter(number=bad)
    with pytest.raises(TypeError):
        chut.es_id_letter(number=12345678)
    assert chut.check(name="verhoeff", digits="2363") is True


# =============
# DNI
# =============


@pytest.mark.parametrize(
    "cell",
    ["12345678Z", "12345678-Z", "12345678 Z", "12.345.678-Z", "12345678z", "87654321X"],
)
def test_macie_dni_formats(dni, cell: str) -> None:
    assert dni.matches(cell=cell) == [(0, len(cell))]


@pytest.mark.parametrize(
    "cell",
    [
        #
        # bad letter; no letter (an Argentina DNI); 7 or 9 digits;
        # touching letters or digits; Macie's examples and all zeroes,
        # with their right letters
        #
        "12345678A",
        "12345678",
        "1234567Z",
        "112345678Z",
        "A12345678Z",
        "12345678ZA",
        "12.345.678.Z",
        "99999999R",
        "99.999.999-R",
        "00000000T",
    ],
)
def test_macie_dni_not_a_dni(dni, cell: str) -> None:
    assert dni.matches(cell=cell) == []


def test_macie_dni_in_text(dni) -> None:
    assert dni.matches(cell="DNI: 12345678Z, Madrid") == [(5, 14)]


def test_macie_dni_is_not_a_nie(dni, nie) -> None:
    assert dni.matches(cell="X1234567L") == []
    assert nie.matches(cell="12345678Z") == []


# =============
# NIE
# =============


@pytest.mark.parametrize(
    "cell",
    ["X1234567L", "X-1234567-L", "X 1234567 L", "Y1234567X", "Z7654321H", "x1234567l"],
)
def test_macie_nie_formats(nie, cell: str) -> None:
    assert nie.matches(cell=cell) == [(0, len(cell))]


@pytest.mark.parametrize(
    "cell", ["X1234567A", "W1234567L", "X123456L", "X0000000T", "AX1234567L"]
)
def test_macie_nie_not_a_nie(nie, cell: str) -> None:
    assert nie.matches(cell=cell) == []


def test_macie_es_id_bad_config() -> None:
    for bad in [{}, {"form": "nip"}, {"form": None}]:
        with pytest.raises(MacieException):
            EsIdDetector(config=bad)
    with pytest.raises(TypeError):
        EsIdDetector(config=None)


def test_macie_es_id_bad_cell(dni) -> None:
    with pytest.raises(TypeError):
        dni.matches(cell=None)


# =============
# Aadhaar
# =============


@pytest.mark.parametrize("cell", [AADHAAR, "2345 6789 0124", "2345-6789-0124"])
def test_macie_aadhaar_formats(aadhaar, cell: str) -> None:
    assert aadhaar.matches(cell=cell) == [(0, len(cell))]


@pytest.mark.parametrize(
    "cell",
    [
        #
        # Verhoeff-valid, but Aadhaar numbers never start with 0 or 1
        #
        "123456789010",
        "023456789014",
        "234567890125",
        "2345 6789-0124",
        "23456 789 0124",
        "1234567890124",
    ],
)
def test_macie_aadhaar_not_an_aadhaar(aadhaar, cell: str) -> None:
    assert aadhaar.matches(cell=cell) == []


# =============
# catalog entries and identifiers
# =============


def test_macie_es_in_catalog(catalog) -> None:
    dni = catalog.identifier(name="SPAIN_DNI_NUMBER")
    nie = catalog.identifier(name="SPAIN_NIE_NUMBER")
    aadhaar = catalog.identifier(name="INDIA_AADHAAR_NUMBER")
    assert "dni" in dni["keywords"] and "nie" not in dni["keywords"]
    #
    # the NIE uses Spain's taxpayer list, shared with NIF and CIF
    #
    assert "nie" in nie["keywords"] and "nif" in nie["keywords"]
    assert aadhaar["keywords"] == ["aadhaar", "aadhar", "adhaar", "uidai"]
    assert dni["fidelity"] == "B"
    for e in [dni, nie, aadhaar]:
        assert e["category"] == "PERSONAL_INFORMATION"
        assert e["keyword_mode"] == "required"
        assert e["severity"] == "1:HIGH"


@pytest.mark.parametrize(
    "name, cell, header, n",
    [
        ("SPAIN_DNI_NUMBER", "12345678Z", "dni", 1),
        ("SPAIN_DNI_NUMBER", "12345678Z", "notes", 0),
        ("SPAIN_DNI_NUMBER", "documento nacional de identidad 12345678Z", "x", 1),
        ("SPAIN_NIE_NUMBER", "nie X1234567L", "x", 1),
        ("SPAIN_NIE_NUMBER", "X1234567L", "dni", 0),
        ("INDIA_AADHAAR_NUMBER", "2345 6789 0124", "aadhaar", 1),
        ("INDIA_AADHAAR_NUMBER", "uidai 2345 6789 0124", "x", 1),
        ("INDIA_AADHAAR_NUMBER", AADHAAR, "notes", 0),
    ],
)
def test_macie_es_in_identifiers(
    catalog, name: str, cell: str, header: str, n: int
) -> None:
    assert (
        _mdi(catalog, name).occurrences(cell=cell, header=header, allow_lists=NO_ALLOW)
        == n
    )


def test_macie_es_short_keywords_match_inside_words(catalog) -> None:
    #
    # keywords match as substrings (transpile-design.md, interpretations
    # 3 and 10), so "nie" is found in "niece" and "tin" in "destination".
    # That over-reports keyword presence; the number must still pass its
    # control letter
    #
    nie = _mdi(catalog, "SPAIN_NIE_NUMBER")
    assert nie.occurrences(cell="X1234567L", header="niece", allow_lists=NO_ALLOW) == 1
    assert (
        nie.occurrences(
            cell="destination X1234567L", header="notes", allow_lists=NO_ALLOW
        )
        == 1
    )
    assert nie.occurrences(cell="X1234567A", header="niece", allow_lists=NO_ALLOW) == 0
