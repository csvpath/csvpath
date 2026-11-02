"""managed identifier stand-ins, low level: the Luhn check, the catalog,
the credit card detector, the "near" keyword rule, and ManagedIdentifier.
The card numbers were generated outside ChecksumUtility and pass Luhn;
none is an issuer test number."""

import json

import pytest

from csvpath.macie.allow_list_set import AllowListSet
from csvpath.macie.checksum_utility import ChecksumUtility as chut
from csvpath.macie.detectors import DETECTORS
from csvpath.macie.detectors.credit_card_detector import CreditCardDetector
from csvpath.macie.keyword_utility import KeywordUtility as keut
from csvpath.macie.macie_exceptions import MacieException
from csvpath.macie.managed_catalog import ManagedCatalog
from csvpath.macie.managed_identifier import ManagedIdentifier
from csvpath.macie.severity_levels import SeverityLevels

CARDS = {
    "visa16": "4532777777777774",
    "visa13": "4929777777778",
    "visa19": "4716777777777777773",
    "american_express": "371477777777773",
    "mastercard": "5425777777777771",
    "mastercard_2_series": "2223777777777772",
    "discover": "6011777777777779",
    "jcb": "3530777777777778",
    "diners_club": "30567777777774",
    "unionpay": "6250777777777779",
    "dankort": "5019777777777773",
}
VISA = CARDS["visa16"]
NO_ALLOW = AllowListSet()


def _bad_digit(n: str) -> str:
    return n[:-1] + str((int(n[-1]) + 1) % 10)


@pytest.fixture(scope="module")
def catalog() -> ManagedCatalog:
    return ManagedCatalog.load()


@pytest.fixture(scope="module")
def detector(catalog) -> CreditCardDetector:
    return CreditCardDetector(config=catalog.detector(name="credit_card"))


# =============
# Luhn
# =============


@pytest.mark.parametrize("n", list(CARDS.values()) + ["0", "18", "79927398713"])
def test_macie_luhn_valid(n: str) -> None:
    assert chut.luhn(digits=n) is True


@pytest.mark.parametrize(
    "n", [_bad_digit(v) for v in CARDS.values()] + ["1", "79927398710"]
)
def test_macie_luhn_invalid(n: str) -> None:
    assert chut.luhn(digits=n) is False


@pytest.mark.parametrize("bad", ["", "12a4", "4532 7777", "١٢٣"])
def test_macie_luhn_bad_input(bad: str) -> None:
    with pytest.raises(ValueError):
        chut.luhn(digits=bad)
    with pytest.raises(TypeError):
        chut.luhn(digits=None)


# =============
# catalog
# =============


def test_macie_catalog_packaged(catalog) -> None:
    assert catalog.names == [
        "CREDIT_CARD_NUMBER",
        "CREDIT_CARD_NUMBER_(NO_KEYWORD)",
        "USA_SOCIAL_SECURITY_NUMBER",
        "USA_NATIONAL_PROVIDER_IDENTIFIER",
    ]
    cc = catalog.identifier(name="CREDIT_CARD_NUMBER")
    assert cc["category"] == "FINANCIAL_INFORMATION"
    assert cc["keyword_mode"] == "required"
    assert cc["severity"] == "1:HIGH"
    assert len(cc["keywords"]) == 37
    assert "visa" in cc["keywords"]
    nk = catalog.identifier(name="CREDIT_CARD_NUMBER_(NO_KEYWORD)")
    assert nk["keyword_mode"] == "absent"
    assert nk["keywords"] == cc["keywords"]
    assert len(catalog.detector(name="credit_card")["exclusions"]) == 55
    assert set(DETECTORS) == {"credit_card", "us_ssn", "us_npi"}
    #
    # every detector the catalog names exists, and every detector is used
    #
    used = {catalog.identifier(name=n)["detector"] for n in catalog.names}
    assert used == set(DETECTORS)


def test_macie_catalog_unknown_names(catalog) -> None:
    #
    # NAME is machine-learning based in Macie: no stand-in
    #
    assert catalog.has(name="NAME") is False
    with pytest.raises(MacieException):
        catalog.identifier(name="NAME")
    with pytest.raises(MacieException):
        catalog.detector(name="ssn")


def _write_catalog(tmp_path, change) -> str:
    with open(ManagedCatalog.DEFAULT, encoding="utf-8") as f:
        c = json.load(f)
    change(c)
    p = tmp_path / "catalog.json"
    p.write_text(json.dumps(c), encoding="utf-8")
    return str(p)


@pytest.mark.parametrize(
    "change",
    [
        lambda c: c.update(version=2),
        lambda c: c.pop("detectors"),
        lambda c: c["identifiers"]["CREDIT_CARD_NUMBER"].pop("severity"),
        lambda c: c["identifiers"]["CREDIT_CARD_NUMBER"].update(keyword_mode="maybe"),
        lambda c: c["identifiers"]["CREDIT_CARD_NUMBER"].update(keywords_from="x"),
        lambda c: c["identifiers"]["CREDIT_CARD_NUMBER"].update(detector="x"),
        lambda c: c["identifiers"]["CREDIT_CARD_NUMBER"].update(distance=0),
        lambda c: c["identifiers"]["CREDIT_CARD_NUMBER"].update(severity="HIGH"),
        lambda c: c["keyword_lists"]["credit_card"].update(keywords=[]),
        lambda c: c["keyword_lists"]["credit_card"]["keywords"].append("a|b"),
    ],
)
def test_macie_catalog_bad_entries_fail_on_load(tmp_path, change) -> None:
    with pytest.raises(MacieException):
        ManagedCatalog.load(path=_write_catalog(tmp_path, change))


def test_macie_catalog_unreadable(tmp_path) -> None:
    p = tmp_path / "bad.json"
    p.write_text("{not json", encoding="utf-8")
    with pytest.raises(MacieException):
        ManagedCatalog.load(path=str(p))
    with pytest.raises(MacieException):
        ManagedCatalog.load(path=str(tmp_path / "missing.json"))
    with pytest.raises(ValueError):
        ManagedCatalog.load(path="")


# =============
# credit card detector
# =============


@pytest.mark.parametrize("brand, n", list(CARDS.items()))
def test_macie_card_each_brand(detector, brand: str, n: str) -> None:
    assert detector.matches(cell=n) == [(0, len(n))]
    expected = "visa" if brand.startswith("visa") else brand
    expected = "mastercard" if brand.startswith("mastercard") else expected
    assert detector.brand(digits=n) == expected


def test_macie_card_bad_check_digit(detector) -> None:
    for n in CARDS.values():
        assert detector.matches(cell=_bad_digit(n)) == []


@pytest.mark.parametrize(
    "n",
    [
        #
        # pass Luhn, but no brand has this prefix and length
        #
        "1234567812345670",
        "9000000000000001",
        #
        # Amex prefix at 16 digits
        #
        "3400000000000000",
    ],
)
def test_macie_card_unknown_prefix_or_length(detector, n: str) -> None:
    assert chut.luhn(digits=n) is True
    assert detector.matches(cell=n) == []


def test_macie_card_issuer_test_numbers_are_excluded(detector) -> None:
    assert chut.luhn(digits="4111111111111111") is True
    assert detector.matches(cell="4111111111111111") == []
    assert detector.matches(cell="4111 1111 1111 1111") == []
    assert detector.matches(cell="5555555555554444") == []


@pytest.mark.parametrize(
    "cell",
    [
        "4532 7777 7777 7774",
        "4532-7777-7777-7774",
        "3714 777777 77773",
        "3056-777777-7774",
        "4716 7777 7777 7777 773",
    ],
)
def test_macie_card_grouped(detector, cell: str) -> None:
    assert detector.matches(cell=cell) == [(0, len(cell))]


@pytest.mark.parametrize(
    "cell",
    [
        "4532 7777-7777 7774",
        "45327 777 7777 7774",
        "4532  7777 7777 7774",
        "4532.7777.7777.7774",
    ],
)
def test_macie_card_irregular_grouping_is_not_a_card(detector, cell: str) -> None:
    assert detector.matches(cell=cell) == []


def test_macie_card_digit_boundaries(detector) -> None:
    assert detector.matches(cell=f"9{VISA}") == []
    assert detector.matches(cell=f"{VISA}9") == []
    assert detector.matches(cell=f"x{VISA}y") == [(1, 17)]
    #
    # 20 contiguous digits is not a 13-19 digit sequence
    #
    assert detector.matches(cell=VISA + "0000") == []


def test_macie_card_several_in_one_cell(detector) -> None:
    cell = f"{VISA}, {CARDS['mastercard']} and 4532 7777 7777 7774"
    assert detector.matches(cell=cell) == [(0, 16), (18, 34), (39, 58)]


def test_macie_card_bad_config() -> None:
    with pytest.raises(TypeError):
        CreditCardDetector(config=None)
    for bad in [
        {"min_length": 13, "max_length": 19, "brands": []},
        {
            "min_length": 0,
            "max_length": 19,
            "brands": [{"prefixes": ["4"], "lengths": [16]}],
        },
        {
            "min_length": 13,
            "max_length": 19,
            "brands": [{"prefixes": ["4-55"], "lengths": [16]}],
        },
        {"min_length": 13, "max_length": 19, "brands": [{"prefixes": ["4"]}]},
    ]:
        with pytest.raises(MacieException):
            CreditCardDetector(config=bad)


# =============
# the near keyword rule
# =============


def _near(cell: str, match: str, *keywords: str, distance: int = 30) -> bool:
    start = cell.index(match)
    return keut.near(
        cell=cell,
        match_start=start,
        match_end=start + len(match),
        patterns=keut.patterns(variants=keut.all_variants(keywords=list(keywords))),
        distance=distance,
    )


def test_macie_near_before_and_after() -> None:
    assert _near(f"visa {VISA}", VISA, "visa")
    assert _near(f"{VISA} (visa)", VISA, "visa")


def test_macie_near_distance_is_the_gap() -> None:
    #
    # 30 characters between the keyword and the number still count
    #
    assert _near("visa" + "x" * 30 + VISA, VISA, "visa")
    assert not _near("visa" + "x" * 31 + VISA, VISA, "visa")
    assert _near(VISA + "x" * 30 + "visa", VISA, "visa")
    assert not _near(VISA + "x" * 31 + "visa", VISA, "visa")


def test_macie_near_variants_and_case() -> None:
    assert _near(f"Credit_Card: {VISA}", VISA, "credit card")
    assert _near(f"CREDITCARD {VISA}", VISA, "credit card")


def test_macie_near_bad_input() -> None:
    p = keut.patterns(variants=["visa"])
    with pytest.raises(TypeError):
        keut.near(cell=None, match_start=0, match_end=0, patterns=p, distance=5)
    with pytest.raises(ValueError):
        keut.near(cell="x", match_start=0, match_end=1, patterns=p, distance=0)
    with pytest.raises(ValueError):
        keut.near(cell="x", match_start=0, match_end=2, patterns=p, distance=5)


# =============
# ManagedIdentifier
# =============


def _mdi(catalog, name: str = "CREDIT_CARD_NUMBER") -> ManagedIdentifier:
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


def test_macie_mdi_required_keyword(catalog) -> None:
    cc = _mdi(catalog)
    assert cc.occurrences(cell=VISA, header="card_number", allow_lists=NO_ALLOW) == 1
    assert (
        cc.occurrences(cell=f"visa {VISA}", header="notes", allow_lists=NO_ALLOW) == 1
    )
    assert cc.occurrences(cell=VISA, header="notes", allow_lists=NO_ALLOW) == 0


def test_macie_mdi_absent_keyword_is_the_complement(catalog) -> None:
    cc = _mdi(catalog)
    nk = _mdi(catalog, "CREDIT_CARD_NUMBER_(NO_KEYWORD)")
    for cell, header in [
        (VISA, "card_number"),
        (f"visa {VISA}", "notes"),
        (VISA, "notes"),
        (f"{VISA} {CARDS['jcb']}", "notes"),
    ]:
        both = cc.occurrences(cell=cell, header=header, allow_lists=NO_ALLOW)
        both += nk.occurrences(cell=cell, header=header, allow_lists=NO_ALLOW)
        #
        # every card is reported by exactly one of the two
        #
        assert both == len(cell.split(" ")) - (1 if cell.startswith("visa ") else 0)


def test_macie_mdi_allow_list_on_the_occurrence_text(catalog) -> None:
    allow = AllowListSet()
    allow.add_regex(name="ours", pattern=r"4532[ -]?7777[ -]?7777[ -]?7774")
    cc = _mdi(catalog)
    assert cc.occurrences(cell=VISA, header="card", allow_lists=allow) == 0
    assert (
        cc.occurrences(cell="4532 7777 7777 7774", header="card", allow_lists=allow)
        == 0
    )
    assert cc.occurrences(cell=CARDS["jcb"], header="card", allow_lists=allow) == 1


def test_macie_mdi_bad_input(catalog) -> None:
    e = catalog.identifier(name="CREDIT_CARD_NUMBER")
    args = {
        "name": "CREDIT_CARD_NUMBER",
        "category": e["category"],
        "detector": "credit_card",
        "keyword_mode": "required",
        "keywords": e["keywords"],
        "distance": 30,
        "severity": SeverityLevels.parse(text="1:HIGH"),
        "catalog": catalog,
    }
    for k, v, err in [
        ("name", "", ValueError),
        ("detector", "ssn", MacieException),
        ("keyword_mode", "maybe", MacieException),
        ("keywords", [], MacieException),
        ("keywords", "visa", TypeError),
        ("distance", 0, ValueError),
        ("severity", "1:HIGH", TypeError),
        ("catalog", None, TypeError),
    ]:
        with pytest.raises(err):
            ManagedIdentifier(**{**args, k: v})
    with pytest.raises(TypeError):
        _mdi(catalog).occurrences(cell=None, header="h", allow_lists=NO_ALLOW)
