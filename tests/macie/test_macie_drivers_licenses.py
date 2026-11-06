"""Driver's license stand-ins, the fifth group B step: 17 of Macie's 32
driver's license identifiers as FormatDetector formats, the US one the
union of the states' formats, each tagged with its states (David,
2026-11-05). The other 15 countries are on the worklist."""

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
    ],
)
def test_macie_drivers_license_identifiers(
    catalog, name: str, cell: str, header: str, n: int
) -> None:
    assert (
        _mdi(catalog, name).occurrences(cell=cell, header=header, allow_lists=NO_ALLOW)
        == n
    )
