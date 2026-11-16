"""MaskUtility and ColumnFacts: the masks and column facts a Jev review
of Macie findings is built from (specs/macie/jev-review-build.md). The
facts' wording is the second Jev experiment's."""

import pytest

from csvpath.macie.column_facts import ColumnFacts
from csvpath.macie.util.mask_utility import MaskUtility as maut


def _facts(cells: list[str]) -> ColumnFacts:
    f = ColumnFacts(
        identifier="USA_SOCIAL_SECURITY_NUMBER", column=3, column_name="ssn"
    )
    for c in cells:
        f.add(cell=c, occurrences=1)
    return f


@pytest.mark.parametrize(
    "text, masked",
    [
        ("309-04-7794", "###-##-####"),
        ("RSSMRA85T10A562S", "AAAAAA##A##A###A"),
        ("+1 (212) 555-0148", "+# (###) ###-####"),
        ("Ñandú 7", "AAAAA #"),
        ("", ""),
    ],
)
def test_macie_mask(text: str, masked: str) -> None:
    assert maut.mask(text=text) == masked


def test_macie_mask_cell_keeps_words_without_digits() -> None:
    assert maut.mask_cell(text="ssn on file: 721-99-9913 ok") == (
        "ssn on file: ###-##-#### ok"
    )
    assert maut.mask_cell(text="tax code RSSMRA85T10A562S") == (
        "tax code AAAAAA##A##A###A"
    )
    #
    # documented: a value with no digit is not masked
    #
    assert maut.mask_cell(text="Martha Rivera") == "Martha Rivera"


def test_macie_mask_bad_input() -> None:
    with pytest.raises(TypeError):
        maut.mask(text=None)
    with pytest.raises(TypeError):
        maut.mask_cell(text=5)


def test_macie_column_facts_same_value() -> None:
    f = _facts(["123-45-6789"] * 400)
    assert f.cells == 400
    assert f.distinct == 1
    assert f.facts() == ["Every one of the 400 flagged values is the same value."]
    assert f.samples == ["###-##-####"]


def test_macie_column_facts_few_values() -> None:
    f = _facts([f"415-555-010{i % 9}" for i in range(1400)])
    assert f.distinct == 9
    assert f.facts() == [
        "Only 9 distinct values among 1400 flagged cells: the same few values repeat."
    ]


def test_macie_column_facts_all_different() -> None:
    f = _facts(["309-04-7794", "166-46-2907", "716-90-7411", "644-25-1556"])
    assert f.facts() == ["Every flagged value is different."]
    assert f.consecutive is False
    #
    # samples are kept once per masked shape: four SSNs are one sample
    #
    assert f.samples == ["###-##-####"]
    notes = ColumnFacts(identifier="X", column=1, column_name="notes")
    for c in ["ssn 1", "member ssn 2", "ssn on file 3", "ssn again 4"]:
        notes.add(cell=c, occurrences=1)
    assert len(notes.samples) == ColumnFacts.MAX_SAMPLES


def test_macie_column_facts_consecutive() -> None:
    f = _facts([f"{100234871 + i}" for i in range(900)])
    assert f.consecutive is True
    assert f.facts() == [
        "Every flagged value is different.",
        "The flagged values are consecutive: each is the one before plus one.",
    ]
    #
    # a gap, a repeat, or one cell with words: not consecutive
    #
    assert _facts(["100", "101", "103"]).consecutive is False
    assert _facts(["100", "101", "101", "102"]).consecutive is False
    assert _facts(["100", "101", "ref 102"]).consecutive is False
    assert _facts(["100", "101"]).consecutive is False


def test_macie_column_facts_counts_occurrences_and_cells() -> None:
    f = ColumnFacts(identifier="X", column=1, column_name="notes")
    f.add(cell="EMP-111111 and EMP-222222", occurrences=2)
    f.add(cell="EMP-333333", occurrences=1)
    assert (f.cells, f.occurrences, f.distinct) == (2, 3, 2)
    d = f.to_dict()
    assert d["columnName"] == "notes"
    assert d["why"] is None
    assert (
        ColumnFacts(identifier="X", column=1, column_name="n", why="a keyword").why
        == "a keyword"
    )
    assert d["samples"] == ["AAA-###### and AAA-######", "AAA-######"]
    assert d["facts"] == ["Every flagged value is different."]


def test_macie_column_facts_cap(monkeypatch) -> None:
    monkeypatch.setattr(ColumnFacts, "MAX_DISTINCT", 5)
    f = _facts([f"{i:03d}-00-0000" for i in range(200)])
    assert f.capped is True
    assert f.distinct == 5
    assert f.consecutive is False
    assert f.facts() == [
        "Only at least 5 distinct values among 200 flagged cells: the same few "
        "values repeat."
    ]


def test_macie_column_facts_keeps_no_value() -> None:
    f = _facts(["309-04-7794", "166-46-2907"])
    assert "309-04-7794" not in repr(f.to_dict())


def test_macie_column_facts_bad_input() -> None:
    for kw in [
        {"identifier": "", "column": 1, "column_name": "x"},
        {"identifier": "X", "column": 0, "column_name": "x"},
        {"identifier": "X", "column": True, "column_name": "x"},
        {"identifier": "X", "column": 1, "column_name": "x", "why": " "},
    ]:
        with pytest.raises(ValueError):
            ColumnFacts(**kw)
    with pytest.raises(TypeError):
        ColumnFacts(identifier="X", column=1, column_name=None)
    f = ColumnFacts(identifier="X", column=1, column_name="x")
    with pytest.raises(TypeError):
        f.add(cell=None, occurrences=1)
    for n in [0, -1, True, "1"]:
        with pytest.raises(ValueError):
            f.add(cell="x", occurrences=n)
