"""Phone number stand-ins, the third group B step: PhoneDetector, the
numbering plans in the catalog, and Macie's rule that a number near a
keyword needs no country code and a number with no keyword needs one.
Google's phonenumbers library (a dev dependency, not used by the package)
supplies example numbers for each country, in national, international,
E.164 and 00 forms, which every plan must find."""

import phonenumbers
import pytest
from phonenumbers import PhoneNumberFormat, PhoneNumberType

from csvpath.macie.allow_list_set import AllowListSet
from csvpath.macie.detectors.phone_detector import PhoneDetector
from csvpath.macie.macie_exceptions import MacieException
from csvpath.macie.managed_catalog import ManagedCatalog
from csvpath.macie.managed_identifier import ManagedIdentifier
from csvpath.macie.severity_levels import SeverityLevels

NO_ALLOW = AllowListSet()
#
# region -> (catalog detector, Macie identifier); Macie's PHONE_NUMBER is
# the US and Canada together
#
REGIONS = {
    "GB": ("gb_phone", "UK_PHONE_NUMBER"),
    "FR": ("fr_phone", "FRANCE_PHONE_NUMBER"),
    "DE": ("de_phone", "GERMANY_PHONE_NUMBER"),
    "IT": ("it_phone", "ITALY_PHONE_NUMBER"),
    "ES": ("es_phone", "SPAIN_PHONE_NUMBER"),
    "BR": ("br_phone", "BRAZIL_PHONE_NUMBER"),
    "US": ("us_phone", "PHONE_NUMBER"),
    "CA": ("us_phone", "PHONE_NUMBER"),
}
TYPES = [PhoneNumberType.FIXED_LINE, PhoneNumberType.MOBILE, PhoneNumberType.TOLL_FREE]


@pytest.fixture(scope="module")
def catalog() -> ManagedCatalog:
    return ManagedCatalog.load()


def _detector(catalog, name: str) -> PhoneDetector:
    return PhoneDetector(config=catalog.detector(name=name))


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


def _examples() -> list[tuple[str, str]]:
    out = []
    for region in REGIONS:
        for t in TYPES:
            n = phonenumbers.example_number_for_type(region, t)
            if n is None:
                continue
            for f in [
                PhoneNumberFormat.NATIONAL,
                PhoneNumberFormat.INTERNATIONAL,
                PhoneNumberFormat.E164,
            ]:
                out.append((region, phonenumbers.format_number(n, f)))
            e164 = phonenumbers.format_number(n, PhoneNumberFormat.E164)
            out.append((region, "00" + e164[1:]))
    return out


@pytest.mark.parametrize("region, cell", _examples())
def test_macie_phone_oracle_examples(catalog, region: str, cell: str) -> None:
    detector = _detector(catalog, REGIONS[region][0])
    assert detector.matches(cell=cell) == [(0, len(cell))]


@pytest.mark.parametrize(
    "name, cell",
    [
        ("gb_phone", "+44 (0)20 7946 0958"),
        ("gb_phone", "020.7946.0958"),
        ("us_phone", "1-212-555-0100"),
        ("us_phone", "212.555.0100"),
        ("br_phone", "0 (11) 96123-4567"),
        ("it_phone", "06 1234 5678"),
    ],
)
def test_macie_phone_more_forms(catalog, name: str, cell: str) -> None:
    assert _detector(catalog, name).matches(cell=cell) == [(0, len(cell))]


@pytest.mark.parametrize(
    "name, cell",
    [
        #
        # another country's code; the UK, France and Germany need the
        # trunk 0 in a national number; NANP area codes and exchanges
        # start 2-9; too short; touching letters; two numbers with only a
        # space between read as one
        #
        ("gb_phone", "+33 1 23 45 67 89"),
        ("gb_phone", "20 7946 0958"),
        ("fr_phone", "123456789"),
        ("us_phone", "(212) 155-0100"),
        ("us_phone", "(112) 555-0100"),
        ("de_phone", "030 12"),
        ("es_phone", "412 34 56 78"),
        ("gb_phone", "tel020 7946 0958"),
        ("gb_phone", "020 7946 0958 020 7946 0959"),
    ],
)
def test_macie_phone_not_detected(catalog, name: str, cell: str) -> None:
    assert _detector(catalog, name).matches(cell=cell) == []


def test_macie_phone_country_code_is_keyword_exempt(catalog) -> None:
    d = _detector(catalog, "gb_phone")
    cell = "call +44 20 7946 0958 or 020 7946 0958"
    spans = d.matches(cell=cell)
    assert [d.keyword_exempt(cell=cell, start=s, end=e) for s, e in spans] == [
        True,
        False,
    ]


@pytest.mark.parametrize(
    "cell, header, n",
    [
        #
        # Macie: with a keyword, no country code needed; without one, the
        # number must have its country code
        #
        ("020 7946 0958", "phone", 1),
        ("tel 020 7946 0958", "x", 1),
        ("020 7946 0958", "notes", 0),
        ("+44 20 7946 0958", "notes", 1),
        ("0044 20 7946 0958", "notes", 1),
        ("+44 20 7946 0958 / 020 7946 0958", "notes", 1),
    ],
)
def test_macie_phone_keyword_rule(catalog, cell: str, header: str, n: int) -> None:
    assert (
        _mdi(catalog, "UK_PHONE_NUMBER").occurrences(
            cell=cell, header=header, allow_lists=NO_ALLOW
        )
        == n
    )


def test_macie_phone_brazil_keywords(catalog) -> None:
    br = _mdi(catalog, "BRAZIL_PHONE_NUMBER")
    assert (
        br.occurrences(cell="celular (11) 96123-4567", header="x", allow_lists=NO_ALLOW)
        == 1
    )
    assert (
        br.occurrences(cell="(11) 96123-4567", header="telefone", allow_lists=NO_ALLOW)
        == 1
    )
    #
    # Brazil's extra keywords are not the UK's, but keywords match as
    # substrings: "telefone" holds the shared "tel", "celular" holds no
    # shared keyword ("cell" has two l's)
    #
    uk = _mdi(catalog, "UK_PHONE_NUMBER")
    assert (
        uk.occurrences(cell="telefone 020 7946 0958", header="x", allow_lists=NO_ALLOW)
        == 1
    )
    assert (
        uk.occurrences(cell="celular 020 7946 0958", header="x", allow_lists=NO_ALLOW)
        == 0
    )


def test_macie_phone_catalog(catalog) -> None:
    for _, name in REGIONS.values():
        e = catalog.identifier(name=name)
        assert e["category"] == "PERSONAL_INFORMATION"
        assert e["keyword_mode"] == "required"
        #
        # Macie: phone numbers are LOW for one, MEDIUM from 2, HIGH from 100
        #
        assert e["severity"] == "1:LOW 2:MEDIUM 100:HIGH"
    assert "celular" in catalog.identifier(name="BRAZIL_PHONE_NUMBER")["keywords"]
    assert "celular" not in catalog.identifier(name="UK_PHONE_NUMBER")["keywords"]


def test_macie_phone_bad_config() -> None:
    good = {
        "country_code": "44",
        "trunk": "0",
        "trunk_required": True,
        "nsn_formats": ["#{9}"],
    }
    PhoneDetector(config=good)
    for bad in [
        {**good, "country_code": "0"},
        {**good, "country_code": 44},
        {**good, "trunk": "00"},
        {**good, "trunk_required": "yes"},
        {**good, "trunk": "", "trunk_required": True},
        {**good, "nsn_formats": []},
        {**good, "nsn_formats": ["AIza"]},
    ]:
        with pytest.raises(MacieException):
            PhoneDetector(config=bad)
    with pytest.raises(TypeError):
        PhoneDetector(config=None)
    with pytest.raises(TypeError):
        PhoneDetector(config=good).matches(cell=None)
