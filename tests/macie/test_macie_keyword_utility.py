import pytest

from csvpath.macie.util.keyword_utility import KeywordUtility as keut


def _patterns(*keywords: str) -> list:
    return keut.patterns(variants=keut.all_variants(keywords=list(keywords)))


def _precedes(cell: str, match: str, *keywords: str, distance: int = 50) -> bool:
    start = cell.index(match)
    return keut.precedes(
        cell=cell,
        match_start=start,
        match_end=start + len(match),
        patterns=_patterns(*keywords),
        distance=distance,
    )


def test_macie_keyword_variants() -> None:
    assert keut.variants(keyword=" Employee ID ") == {
        "employee id",
        "employeeid",
        "employee_id",
        "employee-id",
    }
    assert keut.variants(keyword="ssn") == {"ssn"}


def test_macie_keyword_variants_bad_input() -> None:
    with pytest.raises(TypeError):
        keut.variants(keyword=None)
    with pytest.raises(ValueError):
        keut.variants(keyword="  ")
    with pytest.raises(TypeError):
        keut.all_variants(keywords="ssn")
    with pytest.raises(TypeError):
        keut.patterns(variants=None)


def test_macie_keyword_all_variants_are_sorted_and_unique() -> None:
    assert keut.all_variants(keywords=["emp id", "EMP ID", "ssn"]) == [
        "emp id",
        "emp-id",
        "emp_id",
        "empid",
        "ssn",
    ]


@pytest.mark.parametrize(
    "header, expected",
    [
        ("employee_id", True),
        ("EMPLOYEE-ID", True),
        ("EmployeeId", True),
        ("Employee ID (HR)", True),
        ("employee", False),
        ("emp_number", False),
    ],
)
def test_macie_keyword_in_header(header: str, expected: bool) -> None:
    variants = keut.all_variants(keywords=["employee id"])
    assert keut.in_header(header=header, variants=variants) is expected


def test_macie_keyword_in_header_bad_input() -> None:
    with pytest.raises(TypeError):
        keut.in_header(header=None, variants=[])
    with pytest.raises(TypeError):
        keut.in_header(header="h", variants="employee id")


def test_macie_keyword_precedes_within_distance() -> None:
    assert _precedes("emp id EMP-345678 transferred", "EMP-345678", "emp id")
    assert _precedes("Employee ID: EMP-678901", "EMP-678901", "employee id")


def test_macie_keyword_distance_is_keyword_end_to_match_end() -> None:
    #
    # "emp id" + 1 space + 10-char match: distance 11
    #
    cell = "emp id EMP-345678"
    assert _precedes(cell, "EMP-345678", "emp id", distance=11)
    assert not _precedes(cell, "EMP-345678", "emp id", distance=10)


def test_macie_keyword_must_come_before_the_match() -> None:
    assert not _precedes("EMP-345678 emp id", "EMP-345678", "emp id")
    #
    # a keyword that runs into the match does not count
    #
    # ("demp" matches "dEMP", which overlaps the match "EMP-1")
    #
    assert not _precedes("x dEMP-1", "EMP-1", "demp", distance=50)
    #
    # ending where the match starts is fine when a separator is between
    #
    assert _precedes("x demp:EMP-1", "EMP-1", "demp", distance=50)
    #
    # touching letters on either side is not a word
    #
    assert not _precedes("xdemp EMP-1", "EMP-1", "demp", distance=50)
    assert not _precedes("x dempEMP-1", "EMP-1", "demp", distance=50)


def test_macie_keyword_too_far_back() -> None:
    cell = (
        "emp id is in the HR system, see the onboarding packet for details EMP-890123"
    )
    assert not _precedes(cell, "EMP-890123", "emp id")
    assert _precedes(cell, "EMP-890123", "emp id", distance=70)


def test_macie_keyword_nearest_occurrence_counts() -> None:
    cell = "emp id " + "x" * 80 + " emp id EMP-111111"
    assert _precedes(cell, "EMP-111111", "emp id")


def test_macie_keyword_variant_in_cell() -> None:
    assert _precedes("employee_id=EMP-111111", "EMP-111111", "employee id")


def test_macie_keyword_case_insensitive_with_length_changing_case() -> None:
    #
    # "İ".lower() is two characters. positions must still line up.
    #
    cell = "İİİİ emp id EMP-111111"
    assert _precedes(cell, "EMP-111111", "EMP ID", distance=11)
    assert not _precedes(cell, "EMP-111111", "EMP ID", distance=10)


def test_macie_keyword_no_keywords_never_precedes() -> None:
    assert not keut.precedes(
        cell="emp id EMP-1", match_start=7, match_end=12, patterns=[], distance=50
    )


def test_macie_keyword_precedes_bad_input() -> None:
    p = _patterns("emp id")
    with pytest.raises(TypeError):
        keut.precedes(cell=None, match_start=0, match_end=0, patterns=p, distance=5)
    with pytest.raises(TypeError):
        keut.precedes(cell="x", match_start=0, match_end=0, patterns=None, distance=5)
    for d in [0, -1, True, "5"]:
        with pytest.raises(ValueError):
            keut.precedes(cell="x", match_start=0, match_end=1, patterns=p, distance=d)
    with pytest.raises(ValueError):
        keut.precedes(cell="x", match_start=0, match_end=2, patterns=p, distance=5)
    with pytest.raises(ValueError):
        keut.precedes(cell="xy", match_start=2, match_end=1, patterns=p, distance=5)


@pytest.mark.parametrize(
    "header, expected",
    [
        #
        # the third live probe (2026-11-15): Macie matched these as words
        #
        ("ssn", True),
        ("customer_ssn", True),
        ("SSN (US)", True),
        ("ssn-2", True),
        ("ssnumber", False),
        ("myssn", False),
    ],
)
def test_macie_keyword_in_header_is_a_word(header: str, expected: bool) -> None:
    assert keut.in_header(header=header, variants=["ssn"]) is expected


def test_macie_keyword_in_cell_is_a_word() -> None:
    assert _precedes("ssn 123-45-6789", "123-45-6789", "ssn")
    assert _precedes("SSN:123-45-6789", "123-45-6789", "ssn")
    assert not _precedes("myssn 123-45-6789", "123-45-6789", "ssn")
    assert not _precedes("ssnumber 123-45-6789", "123-45-6789", "ssn")


def test_macie_keyword_edge_without_a_letter_needs_no_boundary() -> None:
    #
    # "dl#" ends in "#": a digit right after it does not make it part of a
    # longer word
    #
    assert keut.is_word(text="dl#123", start=0, end=3)
    assert not keut.is_word(text="xdl#123", start=1, end=4)
    assert keut.is_word(text="a dl# b", start=2, end=5)


def test_macie_keyword_is_word_bad_input() -> None:
    with pytest.raises(TypeError):
        keut.is_word(text=None, start=0, end=1)
    for start, end in [(0, 0), (-1, 1), (0, 4), (2, 1)]:
        with pytest.raises(ValueError):
            keut.is_word(text="abc", start=start, end=end)
