"""Birth date and card expiration stand-ins, the fourth group B step:
DateDetector's birth and expiry forms, and the catalog entries."""

import pytest

from csvpath.macie.allow_list_set import AllowListSet
from csvpath.macie.detectors.date_detector import DateDetector
from csvpath.macie.macie_exceptions import MacieException
from csvpath.macie.managed_catalog import ManagedCatalog
from csvpath.macie.managed_identifier import ManagedIdentifier
from csvpath.macie.severity_levels import SeverityLevels

NO_ALLOW = AllowListSet()
BIRTH = DateDetector(config={"form": "birth"})
EXPIRY = DateDetector(config={"form": "expiry"})


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
        "5/11/1985",
        "11/5/1985",
        "25/12/1985",
        "12/25/1985",
        "05-11-85",
        "05 11 1985",
        "1985-11-05",
        "1985/11/05",
        "5 Nov 1985",
        "05-nov-85",
        "5 November 1985",
        "November 5, 1985",
        "Nov 5 1985",
        "1985-Nov-05",
        "19851105",
        "05111985",
        "29/02/2000",
        "29/02/00",
    ],
)
def test_macie_birth_date_formats(cell: str) -> None:
    assert BIRTH.matches(cell=cell) == [(0, len(cell))]


@pytest.mark.parametrize(
    "cell",
    [
        #
        # not real dates; mixed separators; dots (Macie lists spaces,
        # slashes and hyphens); a year out of range; a month and year only;
        # touching letters or digits
        #
        "31/02/1985",
        "13/13/1985",
        "29/02/1985",
        "5/11-1985",
        "05.11.1985",
        "5/11/1885",
        "Nov 1985",
        "x5/11/1985",
        "5/11/19851",
        "12345678",
        "Smarch 5, 1985",
    ],
)
def test_macie_birth_date_not_detected(cell: str) -> None:
    assert BIRTH.matches(cell=cell) == []


def test_macie_birth_date_one_occurrence_per_date() -> None:
    #
    # 05 11 1985 fits more than one shape; it is one date
    #
    assert BIRTH.matches(cell="born 05 11 1985, Leeds") == [(5, 15)]
    assert len(BIRTH.matches(cell="5/11/1985 and 1990-01-02")) == 2


@pytest.mark.parametrize(
    "cell",
    [
        "02/26",
        "02/2026",
        "2-26",
        "Feb 2026",
        "February 2026",
        "feb-26",
        "Feb26",
        "26-Feb",
        "expY=2026, expM=02",
        "expM=02;expY=26",
        "exp y = 2026 exp m = 2",
    ],
)
def test_macie_expiry_formats(cell: str) -> None:
    assert EXPIRY.matches(cell=cell) == [(0, len(cell))]


@pytest.mark.parametrize(
    "cell",
    [
        "13/26",
        "00/26",
        "02/1985",
        "02 26",
        "02.26",
        #
        # part of a full date is not an expiry date
        #
        "12/25/2026",
        "05-Nov-1985",
        "expY=2026",
    ],
)
def test_macie_expiry_not_detected(cell: str) -> None:
    assert EXPIRY.matches(cell=cell) == []


def test_macie_date_bad_config() -> None:
    with pytest.raises(TypeError):
        DateDetector(config=None)
    for bad in [{}, {"form": "issue"}]:
        with pytest.raises(MacieException):
            DateDetector(config=bad)
    with pytest.raises(TypeError):
        BIRTH.matches(cell=None)


def test_macie_dates_catalog(catalog) -> None:
    dob = catalog.identifier(name="DATE_OF_BIRTH")
    exp = catalog.identifier(name="CREDIT_CARD_EXPIRATION")
    assert dob["category"] == "PERSONAL_INFORMATION"
    assert exp["category"] == "FINANCIAL_INFORMATION"
    #
    # Macie: both LOW for one, MEDIUM from 2, HIGH from 100
    #
    for e in [dob, exp]:
        assert e["severity"] == "1:LOW 2:MEDIUM 100:HIGH"
        assert e["keyword_mode"] == "required"
    assert dob["keywords"] == [
        "bday",
        "b-day",
        "birth date",
        "birthday",
        "date of birth",
        "dob",
    ]
    assert exp["keywords"] == ["exp d", "exp m", "exp y", "expiration", "expiry"]


@pytest.mark.parametrize(
    "name, cell, header, n",
    [
        ("DATE_OF_BIRTH", "5/11/1985", "dob", 1),
        ("DATE_OF_BIRTH", "date of birth: 5 Nov 1985", "x", 1),
        ("DATE_OF_BIRTH", "5/11/1985", "joined", 0),
        ("CREDIT_CARD_EXPIRATION", "02/26", "expiry", 1),
        ("CREDIT_CARD_EXPIRATION", "expiration Feb 2026", "x", 1),
        #
        # the keyword form carries its own keywords (expY is "exp y"),
        # inside the occurrence where nearness is not measured, so it is
        # keyword exempt
        #
        ("CREDIT_CARD_EXPIRATION", "expY=2026, expM=02", "notes", 1),
        ("CREDIT_CARD_EXPIRATION", "02/26", "notes", 0),
    ],
)
def test_macie_dates_identifiers(
    catalog, name: str, cell: str, header: str, n: int
) -> None:
    assert (
        _mdi(catalog, name).occurrences(cell=cell, header=header, allow_lists=NO_ALLOW)
        == n
    )
