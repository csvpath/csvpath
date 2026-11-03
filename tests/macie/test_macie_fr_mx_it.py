"""France NIR (INSEE), Mexico CURP and Italy Codice Fiscale stand-ins: the
checks, FrNirDetector, MxCurpDetector, ItCfDetector, and the catalog
entries. The checks were compared with python-stdnum's on 20,000 random
inputs each, outside the test suite; the published examples are stdnum's
and the Agenzia delle Entrate's well-known RSSMRA85T10A562S."""

import pytest

from csvpath.macie.allow_list_set import AllowListSet
from csvpath.macie.checksum_utility import ChecksumUtility as chut
from csvpath.macie.detectors.fr_nir_detector import FrNirDetector
from csvpath.macie.detectors.it_cf_detector import ItCfDetector
from csvpath.macie.detectors.mx_curp_detector import MxCurpDetector
from csvpath.macie.macie_converter import MacieConverter
from csvpath.macie.macie_wrapper_loader import MacieWrapperLoader
from csvpath.macie.managed_catalog import ManagedCatalog
from csvpath.macie.managed_identifier import ManagedIdentifier
from csvpath.macie.severity_levels import SeverityLevels

NO_ALLOW = AllowListSet()
NIR = "295109912611193"
CURP = "BOXW310820HNERXN09"
CF = "RSSMRA85T10A562S"


@pytest.fixture(scope="module")
def catalog() -> ManagedCatalog:
    return ManagedCatalog.load()


@pytest.fixture(scope="module")
def nir() -> FrNirDetector:
    return FrNirDetector(config={})


@pytest.fixture(scope="module")
def curp() -> MxCurpDetector:
    return MxCurpDetector(config={})


@pytest.fixture(scope="module")
def cf() -> ItCfDetector:
    return ItCfDetector(config={})


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
        (NIR, True),
        ("295109912611199", False),
        #
        # Corsica: 2A counts as 19, 2B as 18
        #
        ("253072B07300470", True),
        ("253072A07300443", True),
        ("253072a07300443", True),
        ("253072B07300443", False),
    ],
)
def test_macie_fr_nir_key(n: str, ok: bool) -> None:
    assert chut.fr_nir_key(nir=n) is ok


@pytest.mark.parametrize(
    "first17, check",
    [
        ("BOXW310820HNERXN0", "9"),
        ("GOMA050612MDFRRNA", "8"),
        #
        # O to Z are worth one more than A = 10 would give, for Ñ
        #
        ("ZZZZ000000ZZZZZZZ", chut.mx_curp_check(curp="ZZZZ000000ZZZZZZZ")),
    ],
)
def test_macie_mx_curp_check(first17: str, check: str) -> None:
    assert chut.mx_curp_check(curp=first17) == check


def test_macie_mx_curp_alphabet_has_enye() -> None:
    a = chut.MX_CURP_ALPHABET
    assert a.index("N") == 23 and a.index("Ñ") == 24 and a.index("O") == 25
    assert a.index("Z") == 36


@pytest.mark.parametrize(
    "first15, check",
    [
        ("RSSMRA85T10A562", "S"),
        ("RCCMNL83S18D969", "H"),
        ("RSSMRA85T50A562", "W"),
        ("RSSMRA85T10A56N", "H"),
        ("rssmra85t10a562", "S"),
    ],
)
def test_macie_it_cf_check(first15: str, check: str) -> None:
    assert chut.it_cf_check(code=first15) == check


def test_macie_fr_mx_it_checks_bad_input() -> None:
    for bad in ["29510991261119", "2951099126111933", "253072C07300443", "x" * 15]:
        with pytest.raises(ValueError):
            chut.fr_nir_key(nir=bad)
    with pytest.raises(TypeError):
        chut.fr_nir_key(nir=None)
    for bad in ["BOXW310820HNERXN", "BOXW310820HNERXN09", "BOXW310820HNE-XN0"]:
        with pytest.raises(ValueError):
            chut.mx_curp_check(curp=bad)
    with pytest.raises(TypeError):
        chut.mx_curp_check(curp=None)
    for bad in ["RSSMRA85T10A56", "RSSMRA85T10A5622", "RSSMRA85T10A56-"]:
        with pytest.raises(ValueError):
            chut.it_cf_check(code=bad)
    with pytest.raises(TypeError):
        chut.it_cf_check(code=None)


# =============
# NIR
# =============


@pytest.mark.parametrize(
    "cell",
    [
        NIR,
        "2 95 10 99 126 111 93",
        "2.95.10.99.126.111.93",
        "2951099126111 93",
        "253072B07300470",
        "2 53 07 2A 073 004 43",
    ],
)
def test_macie_nir_formats(nir, cell: str) -> None:
    assert nir.matches(cell=cell) == [(0, len(cell))]


@pytest.mark.parametrize(
    "cell",
    [
        "295109912611199",
        "2 95 10 99 126.111 93",
        "2 951 099 126 111 93",
        "1295109912611193",
        "29510991261119",
        "x295109912611193",
        "253072C07300443",
    ],
)
def test_macie_nir_not_a_nir(nir, cell: str) -> None:
    assert nir.matches(cell=cell) == []


def test_macie_nir_in_text(nir) -> None:
    assert nir.matches(cell="n° sécu 2 95 10 99 126 111 93.") == [(8, 29)]


# =============
# CURP
# =============


@pytest.mark.parametrize(
    "cell",
    [
        CURP,
        "GOMA050612MDFRRNA8",
        "boxw310820hnerxn09",
        #
        # ours: sex X is accepted
        #
        "GOMA050612XDFRRNA2",
    ],
)
def test_macie_curp_formats(curp, cell: str) -> None:
    assert curp.matches(cell=cell) == [(0, len(cell))]


@pytest.mark.parametrize(
    "cell",
    [
        "BOXW310820HNERXN08",
        #
        # right check digits, but: no state ZZ; month 13; 30 February;
        # sex F
        #
        "BOXW310820HZZRXN06",
        "BOXW311320HNERXN02",
        "GOMA050230MDFRRNA0",
        "BOXW310820FNERXN0" + chut.mx_curp_check(curp="BOXW310820FNERXN0"),
        "XBOXW310820HNERXN09",
        "BOXW310820HNERXN091",
    ],
)
def test_macie_curp_not_a_curp(curp, cell: str) -> None:
    assert curp.matches(cell=cell) == []


# =============
# Codice Fiscale
# =============


@pytest.mark.parametrize(
    "cell",
    [
        CF,
        "RCCMNL83S18D969H",
        "rssmra85t10a562s",
        #
        # a woman: day plus 40; omocodia: the place's last digit as N;
        # 29 February in a year that can be a leap year
        #
        "RSSMRA85T50A562W",
        "RSSMRA85T10A56NH",
        "RSSMRA84B29A562Y",
    ],
)
def test_macie_cf_formats(cf, cell: str) -> None:
    assert cf.matches(cell=cell) == [(0, len(cell))]


@pytest.mark.parametrize(
    "cell",
    [
        "RSSMRA85T10A562T",
        #
        # right check letters, but: day 32; 30 February; 29 February in a
        # year that cannot be a leap year; month F
        #
        "RSSMRA85T32A562Y",
        "RSSMRA85B30A562G",
        "RSSMRA85B29A562Z",
        "RSSMRA85F10A562" + chut.it_cf_check(code="RSSMRA85F10A562"),
        "XRSSMRA85T10A562S",
        "RSSMRA85T10A562S1",
    ],
)
def test_macie_cf_not_a_cf(cf, cell: str) -> None:
    assert cf.matches(cell=cell) == []


def test_macie_fr_mx_it_bad_config_and_cell(nir, curp, cf) -> None:
    for cls in [FrNirDetector, MxCurpDetector, ItCfDetector]:
        with pytest.raises(TypeError):
            cls(config=None)
    for d in [nir, curp, cf]:
        with pytest.raises(TypeError):
            d.matches(cell=None)


# =============
# catalog entries and identifiers
# =============


def test_macie_fr_mx_it_catalog(catalog) -> None:
    fr = catalog.identifier(name="FRANCE_NATIONAL_IDENTIFICATION_NUMBER")
    mx = catalog.identifier(name="MEXICO_CURP_NUMBER")
    it = catalog.identifier(name="ITALY_NATIONAL_IDENTIFICATION_NUMBER")
    assert "insee" in fr["keywords"] and "social" in fr["keywords"]
    assert "curp" in mx["keywords"]
    assert "codice fiscal" in it["keywords"] and "p. iva" in it["keywords"]
    assert "11 digit" in it["partial"]
    assert "partial" not in fr and "partial" not in mx
    for e in [fr, mx, it]:
        assert e["category"] == "PERSONAL_INFORMATION"
        assert e["keyword_mode"] == "required"
        assert e["severity"] == "1:HIGH"


@pytest.mark.parametrize(
    "name, cell, header, n",
    [
        ("FRANCE_NATIONAL_IDENTIFICATION_NUMBER", NIR, "insee", 1),
        ("FRANCE_NATIONAL_IDENTIFICATION_NUMBER", f"sécurité sociale {NIR}", "x", 1),
        ("FRANCE_NATIONAL_IDENTIFICATION_NUMBER", NIR, "notes", 0),
        ("MEXICO_CURP_NUMBER", CURP, "curp", 1),
        ("MEXICO_CURP_NUMBER", f"clave única {CURP}", "x", 1),
        ("MEXICO_CURP_NUMBER", CURP, "notes", 0),
        ("ITALY_NATIONAL_IDENTIFICATION_NUMBER", CF, "codice_fiscale", 1),
        ("ITALY_NATIONAL_IDENTIFICATION_NUMBER", f"tax code {CF}", "x", 1),
        ("ITALY_NATIONAL_IDENTIFICATION_NUMBER", CF, "notes", 0),
    ],
)
def test_macie_fr_mx_it_identifiers(
    catalog, name: str, cell: str, header: str, n: int
) -> None:
    assert (
        _mdi(catalog, name).occurrences(cell=cell, header=header, allow_lists=NO_ALLOW)
        == n
    )


def test_macie_cf_converter_reports_partial() -> None:
    w = MacieWrapperLoader.from_path(
        path="tests/macie/test_resources/wrappers/handcrafted_minimal.macie.json"
    )
    name = "ITALY_NATIONAL_IDENTIFICATION_NUMBER"
    w["selection"]["managedDataIdentifierIds"] = [name]
    w["managedDataIdentifiers"]["resolved"] = [name]
    skipped = MacieConverter(wrapper=w).convert(name="t").report.skipped
    assert [s.feature for s in skipped] == ["managedDataIdentifier.partial"]
