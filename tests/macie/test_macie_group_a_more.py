"""Germany identity card, France health insurance number and card
magnetic stripe stand-ins: the ICAO check, DeIdDetector,
MagStripeDetector, and the catalog entries. The ICAO check values are the
ICAO 9303 specimen's (L898902C<3, 690806 1, 940623 6) and the German
specimen card's (T220001293)."""

import pytest

from csvpath.macie.allow_list_set import AllowListSet
from csvpath.macie.checksum_utility import ChecksumUtility as chut
from csvpath.macie.detectors.de_id_detector import DeIdDetector
from csvpath.macie.detectors.mag_stripe_detector import MagStripeDetector
from csvpath.macie.managed_catalog import ManagedCatalog
from csvpath.macie.managed_identifier import ManagedIdentifier
from csvpath.macie.severity_levels import SeverityLevels

NO_ALLOW = AllowListSet()
DE_ID = "T220001293"
NIR = "295109912611193"
TRACK1 = "%B4111111111111111^DOE/JOHN^2512101000000000?"
TRACK2 = ";4111111111111111=2512101?"


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
    "text, check",
    [
        ("L898902C<", "3"),
        ("690806", "1"),
        ("940623", "6"),
        ("T22000129", "3"),
        ("t22000129", "3"),
    ],
)
def test_macie_icao_check(text: str, check: str) -> None:
    assert chut.icao_check(text=text) == check


def test_macie_icao_check_bad_input() -> None:
    for bad in ["", "T2200-0129", "T22 000129"]:
        with pytest.raises(ValueError):
            chut.icao_check(text=bad)
    with pytest.raises(TypeError):
        chut.icao_check(text=None)


@pytest.mark.parametrize(
    "cell",
    #
    # the specimen, lower case, and an older all digit number
    #
    [DE_ID, "t220001293", "122000129" + chut.icao_check(text="122000129")],
)
def test_macie_de_id_formats(cell: str) -> None:
    assert DeIdDetector(config={}).matches(cell=cell) == [(0, len(cell))]


@pytest.mark.parametrize(
    "cell",
    [
        "T220001294",
        #
        # vowels and B D Q S are not used
        #
        "A22000129" + chut.icao_check(text="A22000129"),
        "S22000129" + chut.icao_check(text="S22000129"),
        "T22000129",
        "T2200012934",
        "XT220001293",
    ],
)
def test_macie_de_id_not_detected(cell: str) -> None:
    assert DeIdDetector(config={}).matches(cell=cell) == []


@pytest.mark.parametrize(
    "cell",
    [
        TRACK1,
        "B4111111111111111^DOE/JOHN^25121010000",
        TRACK2,
        "4111111111111111=25121010000000000",
    ],
)
def test_macie_mag_stripe_formats(cell: str) -> None:
    assert MagStripeDetector(config={}).matches(cell=cell) == [(0, len(cell))]


@pytest.mark.parametrize(
    "cell",
    [
        #
        # bad Luhn; month 13; no service code; no name separators; a card
        # number alone is the credit card identifier's, not this one's
        #
        ";4111111111111112=2512101?",
        ";4111111111111111=2513101?",
        ";4111111111111111=2512?",
        "%B4111111111111111 DOE JOHN 2512101?",
        "4111111111111111",
    ],
)
def test_macie_mag_stripe_not_detected(cell: str) -> None:
    assert MagStripeDetector(config={}).matches(cell=cell) == []


def test_macie_mag_stripe_both_tracks_in_one_cell() -> None:
    cell = f"{TRACK1}{TRACK2}"
    assert MagStripeDetector(config={}).matches(cell=cell) == [
        (0, len(TRACK1)),
        (len(TRACK1), len(cell)),
    ]


def test_macie_group_a_more_bad_input() -> None:
    for cls in [DeIdDetector, MagStripeDetector]:
        with pytest.raises(TypeError):
            cls(config=None)
        with pytest.raises(TypeError):
            cls(config={}).matches(cell=None)


def test_macie_group_a_more_catalog(catalog) -> None:
    de = catalog.identifier(name="GERMANY_NATIONAL_IDENTIFICATION_NUMBER")
    fr = catalog.identifier(name="FRANCE_HEALTH_INSURANCE_NUMBER")
    mag = catalog.identifier(name="CREDIT_CARD_MAGNETIC_STRIPE")
    assert "personalausweis" in de["keywords"]
    assert fr["detector"] == "fr_nir"
    assert fr["keywords"] == ["carte d'assuré social", "carte vitale", "insurance card"]
    assert mag["category"] == "FINANCIAL_INFORMATION"
    assert "magstripe" in mag["keywords"]
    for e in [de, fr, mag]:
        assert e["keyword_mode"] == "required"
        assert e["severity"] == "1:HIGH"


@pytest.mark.parametrize(
    "name, cell, header, n",
    [
        ("GERMANY_NATIONAL_IDENTIFICATION_NUMBER", DE_ID, "ausweisnummer", 1),
        ("GERMANY_NATIONAL_IDENTIFICATION_NUMBER", DE_ID, "notes", 0),
        #
        # the same NIR is a health insurance number near health keywords,
        # and a national identification number near INSEE keywords
        #
        ("FRANCE_HEALTH_INSURANCE_NUMBER", f"carte vitale {NIR}", "x", 1),
        ("FRANCE_HEALTH_INSURANCE_NUMBER", f"insee {NIR}", "x", 0),
        ("FRANCE_NATIONAL_IDENTIFICATION_NUMBER", f"insee {NIR}", "x", 1),
        ("CREDIT_CARD_MAGNETIC_STRIPE", TRACK2, "swipe_data", 1),
        ("CREDIT_CARD_MAGNETIC_STRIPE", TRACK2, "notes", 0),
    ],
)
def test_macie_group_a_more_identifiers(
    catalog, name: str, cell: str, header: str, n: int
) -> None:
    assert (
        _mdi(catalog, name).occurrences(cell=cell, header=header, allow_lists=NO_ALLOW)
        == n
    )
