"""GPS coordinates and HTTP cookies, the last group B step: two small
validators the format notation does not cover, LatLongDetector and
CookieDetector, and their catalog entries."""

import pytest

from csvpath.macie.allow_list_set import AllowListSet
from csvpath.macie.detectors.cookie_detector import CookieDetector
from csvpath.macie.detectors.lat_long_detector import LatLongDetector
from csvpath.macie.managed_catalog import ManagedCatalog
from csvpath.macie.managed_identifier import ManagedIdentifier
from csvpath.macie.severity_levels import SeverityLevels

NO_ALLOW = AllowListSet()
GPS = LatLongDetector(config={})
COOKIE = CookieDetector(config={})


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
    "cell",
    [
        "41.948614,-87.655311",
        "41.948614, -87.655311",
        "41.948614 -87.655311",
        "+41.9,+87.6",
        "-90.0,-180.0",
        "0.0,0.0",
    ],
)
def test_macie_gps_formats(cell: str) -> None:
    assert GPS.matches(cell=cell) == [(0, len(cell))]


@pytest.mark.parametrize(
    "cell",
    [
        #
        # out of range; DDM and DMS (Macie: not supported); no decimal
        # part; touching letters, digits or dots; a degree sign
        #
        "90.1,10.0",
        "45.0,180.5",
        "41°56.9168'N 87°39.3187'W",
        "41°56'55.0104\"N 87°39'19.1196\"W",
        "41,87",
        "41.9,87",
        "v41.9,87.6",
        "41.9,87.6.1",
        "1.2.3,4.5",
        "41.9°,87.6°",
    ],
)
def test_macie_gps_not_detected(cell: str) -> None:
    assert GPS.matches(cell=cell) == []


def test_macie_gps_in_text() -> None:
    assert GPS.matches(cell="position 41.948614,-87.655311 at noon") == [(9, 29)]


@pytest.mark.parametrize(
    "cell",
    [
        "Set-Cookie: id=TWlrZQ",
        "Cookie: session=3948; lang=en",
        "cookie:a=b",
        'Cookie: a="bc"',
        "Set-Cookie: id=a3fWa; Secure; HttpOnly; Path=/",
    ],
)
def test_macie_cookie_formats(cell: str) -> None:
    assert COOKIE.matches(cell=cell) == [(0, len(cell))]


@pytest.mark.parametrize(
    "cell",
    [
        #
        # not complete: no pair, no name, or no value; another field whose
        # name ends in Cookie; a quoted value with a space
        #
        "Cookie:",
        "Cookie: session=",
        "Cookie: =b",
        "my-Cookie: a=b",
        "X-Set-Cookie: a=b",
        'Cookie: a="b c"',
        "session=3948; lang=en",
    ],
)
def test_macie_cookie_not_detected(cell: str) -> None:
    assert COOKIE.matches(cell=cell) == []


def test_macie_cookie_occurrences() -> None:
    #
    # one header is one occurrence, however many pairs it has; a
    # Set-Cookie's Expires date ends the occurrence at its first comma
    #
    assert COOKIE.matches(cell="see Cookie: a=1; b=2 and Set-Cookie: c=3") == [
        (4, 20),
        (25, 40),
    ]
    cell = "Set-Cookie: id=a3fWa; Expires=Wed, 21 Oct 2015 07:28:00 GMT"
    assert COOKIE.matches(cell=cell) == [(0, 33)]


def test_macie_gps_cookie_bad_input() -> None:
    for cls in [LatLongDetector, CookieDetector]:
        with pytest.raises(TypeError):
            cls(config=None)
        with pytest.raises(TypeError):
            cls(config={}).matches(cell=None)


def test_macie_gps_cookie_catalog(catalog) -> None:
    gps = catalog.identifier(name="LATITUDE_LONGITUDE")
    cookie = catalog.identifier(name="HTTP_COOKIE")
    for e in [gps, cookie]:
        assert e["category"] == "PERSONAL_INFORMATION"
    #
    # Macie: GPS coordinates are LOW for one, MEDIUM from 2, and stay
    # MEDIUM from 100; cookies LOW, MEDIUM from 2, HIGH from 100
    #
    assert gps["severity"] == "1:LOW 2:MEDIUM"
    assert cookie["severity"] == "1:LOW 2:MEDIUM 100:HIGH"
    assert gps["keyword_mode"] == "required"
    assert gps["keywords"] == [
        "coordinate",
        "coordinates",
        "lat long",
        "latitude longitude",
        "position",
    ]
    assert cookie["keyword_mode"] == "none"


@pytest.mark.parametrize(
    "name, cell, header, n",
    [
        ("LATITUDE_LONGITUDE", "41.948614,-87.655311", "coordinates", 1),
        ("LATITUDE_LONGITUDE", "position 41.948614,-87.655311", "x", 1),
        ("LATITUDE_LONGITUDE", "41.948614,-87.655311", "notes", 0),
        ("HTTP_COOKIE", "Cookie: session=3948; lang=en", "notes", 1),
        ("HTTP_COOKIE", "Set-Cookie: id=TWlrZQ", "x", 1),
        ("HTTP_COOKIE", "session=3948; lang=en", "cookie", 0),
    ],
)
def test_macie_gps_cookie_identifiers(
    catalog, name: str, cell: str, header: str, n: int
) -> None:
    assert (
        _mdi(catalog, name).occurrences(cell=cell, header=header, allow_lists=NO_ALLOW)
        == n
    )
