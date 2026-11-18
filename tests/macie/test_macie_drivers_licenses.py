"""Driver's license stand-ins, the fifth group B step: Macie's 32
driver's license identifiers as FormatDetector formats, the US one the
union of the states' formats, each tagged with its states (David,
2026-11-05). 17 came first (pair 21); the other 15 countries followed
from the worklist (2026-11-18)."""

import pytest

from csvpath.macie.allow_list_set import AllowListSet
from csvpath.macie.detectors.format_detector import FormatDetector
from csvpath.macie.managed_catalog import ManagedCatalog
from csvpath.macie.managed_identifier import ManagedIdentifier
from csvpath.macie.severity_levels import SeverityLevels

NO_ALLOW = AllowListSet()
COUNTRIES = [
    "AUSTRALIA",
    "AUSTRIA",
    "BELGIUM",
    "BULGARIA",
    "CANADA",
    "CROATIA",
    "CYPRUS",
    "CZECHIA",
    "DENMARK",
    "ESTONIA",
    "FRANCE",
    "GERMANY",
    "INDIA",
    "ITALY",
    "SPAIN",
    "UK",
    "US",
    "FINLAND",
    "GREECE",
    "HUNGARY",
    "IRELAND",
    "LATVIA",
    "LITHUANIA",
    "LUXEMBOURG",
    "MALTA",
    "NETHERLANDS",
    "POLAND",
    "PORTUGAL",
    "ROMANIA",
    "SLOVAKIA",
    "SLOVENIA",
    "SWEDEN",
]
STATES = set(
    """AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS
    MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI
    WY""".split()
)


@pytest.fixture(scope="module")
def catalog() -> ManagedCatalog:
    return ManagedCatalog.load()


def _detector(catalog, country: str) -> FormatDetector:
    return FormatDetector(
        config=catalog.detector(name=f"{country.lower()}_drivers_license")
    )


def _ident(country: str) -> str:
    return "DRIVERS_LICENSE" if country == "US" else f"{country}_DRIVERS_LICENSE"


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


def test_macie_drivers_license_detectors_compile(catalog) -> None:
    for c in COUNTRIES:
        _detector(catalog, c)


def test_macie_us_drivers_license_covers_every_state(catalog) -> None:
    formats = catalog.detector(name="us_drivers_license")["formats"]
    used_by = set()
    for f in formats:
        assert set(f) == {"format", "used_by"}
        used_by.update(f["used_by"])
    assert used_by == STATES


@pytest.mark.parametrize(
    "country, cell",
    [
        ("AUSTRIA", "12345678"),
        ("BELGIUM", "1234567890"),
        ("BULGARIA", "123456789"),
        ("CROATIA", "12345678"),
        ("CYPRUS", "123456789012"),
        ("CZECHIA", "EA123456"),
        ("CZECHIA", "EB 123456"),
        ("DENMARK", "12345678"),
        ("ESTONIA", "ET123456"),
        ("FRANCE", "123456789012"),
        ("GERMANY", "B072RRE2I55"),
        ("INDIA", "MH1220110012345"),
        ("INDIA", "MH12 20110012345"),
        ("INDIA", "MH-12-2011-0012345"),
        ("ITALY", "U1A123456X"),
        ("ITALY", "U1 2345678 X"),
        ("SPAIN", "12345678Z"),
        ("SPAIN", "X1234567L"),
        ("UK", "MORGA753116SM9IJ"),
        ("UK", "MORGA753116SM9IJ35"),
        ("UK", "SMIT9851116J99AB"),
        ("AUSTRALIA", "12345678"),
        ("AUSTRALIA", "12 34 5678"),
        ("AUSTRALIA", "A12345"),
        ("CANADA", "A1234-56789-01234"),
        ("CANADA", "A12345678901234"),
        ("CANADA", "P123456789012"),
        ("CANADA", "1234567"),
        ("CANADA", "123456-789"),
        ("FINLAND", "123456-789A"),
        ("FINLAND", "123456-7890"),
        ("GREECE", "123456789"),
        ("HUNGARY", "AB123456"),
        ("IRELAND", "123456ABCD"),
        ("LATVIA", "ABC123456"),
        ("LITHUANIA", "12345678"),
        ("LUXEMBOURG", "123456"),
        ("MALTA", "AB123456"),
        ("MALTA", "12 345 678"),
        ("MALTA", "A1 345678"),
        ("MALTA", "AB123 456"),
        ("NETHERLANDS", "1234567890"),
        ("POLAND", "12345/67/8901"),
        ("POLAND", "12345/67/8901234"),
        ("PORTUGAL", "AB-12345 6"),
        ("PORTUGAL", "AB-123456 7"),
        ("PORTUGAL", "A-123456 7"),
        ("PORTUGAL", "A-12345678 9"),
        ("ROMANIA", "A12345678"),
        ("ROMANIA", "123456789"),
        ("SLOVAKIA", "A1234567"),
        ("SLOVAKIA", "12345678"),
        ("SLOVENIA", "123456789"),
        ("SWEDEN", "123456-7890"),
    ],
)
def test_macie_drivers_license_formats(catalog, country: str, cell: str) -> None:
    assert _detector(catalog, country).matches(cell=cell) == [(0, len(cell))]


@pytest.mark.parametrize(
    "state, cell",
    [
        ("CA", "A1234567"),
        ("FL", "A-123-456-78-901-2"),
        ("FL", "A123456789012"),
        ("IL", "A123-4567-8901"),
        ("NJ", "A1234-56789-01234"),
        ("NY", "123 456 789"),
        ("PA", "12 345 678"),
        ("WA", "WDLAB12CD34E"),
        ("WI", "A123-4567-8901-23"),
        ("NH", "12ABC34567"),
        ("ID", "AB123456C"),
        ("ND", "ABC-12-3456"),
        ("IA", "123AB4567"),
        ("VT", "1234567A"),
        ("WY", "123456-789"),
    ],
)
def test_macie_us_drivers_license_state_formats(catalog, state: str, cell: str) -> None:
    assert _detector(catalog, "US").matches(cell=cell) == [(0, len(cell))]


@pytest.mark.parametrize(
    "country, cell",
    [
        ("AUSTRIA", "1234567"),
        ("CZECHIA", "FA123456"),
        ("ESTONIA", "EE123456"),
        ("GERMANY", "B072RRE2I5"),
        ("ITALY", "1U12345678X"),
        #
        # UK: the month's first digit is 0 1 5 or 6
        #
        ("UK", "MORGA773116SM9IJ"),
        ("US", "WDL12345678"),
        ("US", "A1234567890123456"),
        #
        # Ontario's last group: its second digit is 0 1 5 or 6; and the
        # pieces of a hyphen-joined token are not numbers on their own
        #
        ("CANADA", "A1234-56789-07234"),
        ("FINLAND", "1234567890"),
        ("SWEDEN", "123456-789A"),
        ("HUNGARY", "ABC12345"),
        ("IRELAND", "123456ABC"),
        ("LATVIA", "AB123456"),
        ("LUXEMBOURG", "1234567"),
        ("MALTA", "ABC12345"),
        ("POLAND", "12345/67/89012"),
        ("PORTUGAL", "AB-1234 5"),
        ("PORTUGAL", "A-1234567 8"),
        ("ROMANIA", "AB1234567"),
        ("SLOVAKIA", "AB123456"),
    ],
)
def test_macie_drivers_license_not_detected(catalog, country: str, cell: str) -> None:
    assert _detector(catalog, country).matches(cell=cell) == []


def test_macie_drivers_license_catalog(catalog) -> None:
    for c in COUNTRIES:
        e = catalog.identifier(name=_ident(c))
        assert e["category"] == "PERSONAL_INFORMATION"
        assert e["keyword_mode"] == "required"
        #
        # Macie: driver's licenses are LOW for one, MEDIUM from 2, HIGH
        # from 100
        #
        assert e["severity"] == "1:LOW 2:MEDIUM 100:HIGH"
    assert catalog.identifier(name="FRANCE_DRIVERS_LICENSE")["keywords"] == [
        "permis de conduire"
    ]
    assert "kørekort" in catalog.identifier(name="DENMARK_DRIVERS_LICENSE")["keywords"]
    assert catalog.identifier(name="IRELAND_DRIVERS_LICENSE")["keywords"] == [
        "ceadúnas tiomána"
    ]
    #
    # kept as Macie publishes them
    #
    assert (
        "δεια οδήγησης" in catalog.identifier(name="GREECE_DRIVERS_LICENSE")["keywords"]
    )
    assert (
        "dlno# ajokortti"
        in catalog.identifier(name="SWEDEN_DRIVERS_LICENSE")["keywords"]
    )


def test_macie_drivers_license_every_macie_country(catalog) -> None:
    #
    # Macie's 32 driver's license identifiers, all with a stand-in
    #
    names = [n for n in catalog.names if n.endswith("DRIVERS_LICENSE")]
    assert sorted(names) == sorted(_ident(c) for c in COUNTRIES)
    assert len(names) == 32


@pytest.mark.parametrize(
    "name, cell, header, n",
    [
        ("DRIVERS_LICENSE", "A1234567", "drivers_license", 1),
        ("DRIVERS_LICENSE", "driver's license A1234567", "x", 1),
        ("DRIVERS_LICENSE", "A1234567", "notes", 0),
        ("UK_DRIVERS_LICENSE", "driving licence MORGA753116SM9IJ", "x", 1),
        ("GERMANY_DRIVERS_LICENSE", "B072RRE2I55", "führerschein", 1),
        ("ITALY_DRIVERS_LICENSE", "patente di guida U1 2345678 X", "x", 1),
        #
        # France's only keyword is French
        #
        ("FRANCE_DRIVERS_LICENSE", "driver license 123456789012", "x", 0),
        ("FRANCE_DRIVERS_LICENSE", "permis de conduire 123456789012", "x", 1),
        #
        # 8 digits near an English keyword fit the US, Canada and
        # Australia: their keywords and shapes overlap
        #
        ("DRIVERS_LICENSE", "driver license 12345678", "x", 1),
        ("CANADA_DRIVERS_LICENSE", "driver license 12345678", "x", 1),
        ("AUSTRALIA_DRIVERS_LICENSE", "driver license 12345678", "x", 1),
        ("NETHERLANDS_DRIVERS_LICENSE", "1234567890", "rijbewijsnummer", 1),
        ("POLAND_DRIVERS_LICENSE", "prawo jazdy 12345/67/8901", "x", 1),
        ("PORTUGAL_DRIVERS_LICENSE", "carta de condução AB-12345 6", "x", 1),
        ("IRELAND_DRIVERS_LICENSE", "ceadúnas tiomána 123456ABCD", "x", 1),
        #
        # the EU countries in the backlog have only their own languages'
        # keywords in Macie's list, no English ones
        #
        ("IRELAND_DRIVERS_LICENSE", "driving licence 123456ABCD", "x", 0),
        ("LATVIA_DRIVERS_LICENSE", "vadītāja apliecība ABC123456", "x", 1),
        ("MALTA_DRIVERS_LICENSE", "liċenzja tas-sewqan AB 123 456", "x", 1),
        #
        # Greece's keyword as Macie publishes it lacks its first letter,
        # so as a whole word it is not in άδεια οδήγησης
        #
        ("GREECE_DRIVERS_LICENSE", "adeia odigisis 123456789", "x", 1),
        ("GREECE_DRIVERS_LICENSE", "δεια οδήγησης 123456789", "x", 1),
        ("GREECE_DRIVERS_LICENSE", "άδεια οδήγησης 123456789", "x", 0),
        #
        # Sweden's shape is one of Finland's, and they share keywords
        #
        ("SWEDEN_DRIVERS_LICENSE", "körkort 123456-7890", "x", 1),
        ("FINLAND_DRIVERS_LICENSE", "körkort 123456-7890", "x", 1),
        ("SWEDEN_DRIVERS_LICENSE", "körkort 123456-789A", "x", 0),
        ("FINLAND_DRIVERS_LICENSE", "ajokortti 123456-789A", "x", 1),
    ],
)
def test_macie_drivers_license_identifiers(
    catalog, name: str, cell: str, header: str, n: int
) -> None:
    assert (
        _mdi(catalog, name).occurrences(cell=cell, header=header, allow_lists=NO_ALLOW)
        == n
    )
