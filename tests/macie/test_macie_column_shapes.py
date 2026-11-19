"""ColumnShapes and the case-keeping mask: what the Jev NAME and ADDRESS
check is told about a column (specs/macie/jev-names-addresses-design.md).
No value is kept or sent, only shapes and counts."""

import pytest

from csvpath.macie.column_shapes import ColumnShapes
from csvpath.macie.util.mask_utility import MaskUtility as maut


@pytest.mark.parametrize(
    "text, masked",
    [
        ("Akua Mansa", "Aaaa Aaaaa"),
        ("12 Main St, Springfield, IL 62704", "## Aaaa Aa, Aaaaaaaaaaa, AA #####"),
        ("akua@acme.com", "aaaa@aaaa.aaa"),
        ("Montréal, QC H3B 1A1", "Aaaaaaaa, AA A#A #A#"),
        ("O'Brien-Lund", "A'Aaaaa-Aaaa"),
        ("", ""),
    ],
)
def test_macie_mask_case(text: str, masked: str) -> None:
    assert maut.mask_case(text=text) == masked


def test_macie_mask_case_bad_input() -> None:
    with pytest.raises(TypeError):
        maut.mask_case(text=None)


def _shapes(cells: list[str], name: str = "col") -> ColumnShapes:
    s = ColumnShapes(column=2, column_name=name)
    for c in cells:
        s.add(cell=c)
    return s


def test_macie_column_shapes_counts() -> None:
    s = _shapes(["Akua Mansa", "Omar Haddad", "", "Akua Mansa", "  "])
    assert s.rows == 5
    assert s.filled == 3
    assert s.distinct == 2
    assert s.top() == [("Aaaa Aaaaa", 2), ("Aaaa Aaaaaa", 1)]
    d = s.to_dict()
    assert d["column"] == 2
    assert d["columnName"] == "col"
    assert d["shapes"][0] == {"shape": "Aaaa Aaaaa", "count": 2}
    #
    # no value is kept
    #
    assert "Akua" not in f"{d}"


def test_macie_column_shapes_caps(monkeypatch) -> None:
    monkeypatch.setattr(ColumnShapes, "MAX_SHAPES", 2)
    monkeypatch.setattr(ColumnShapes, "MAX_DISTINCT", 3)
    s = _shapes(["a", "ab", "abc", "abcd", "ab", "zz"])
    assert dict(s.shapes) == {"a": 1, "aa": 3}
    assert s.other == 2
    assert s.distinct == 3
    assert s.distinct_capped is True


@pytest.mark.parametrize(
    "cell, holds",
    [
        #
        # the experiment's address shapes
        #
        ("12 Main St, Springfield, IL 62704", True),
        ("10 Elm Road, London SW1A 2AA", True),
        ("123 Rue Sainte-Catherine, Montréal, QC H3B 1A1", True),
        ("Hauptstraße 5, 10115 Berlin", True),
        ("12 rue de la Paix, 75002 Paris", True),
        ("12 Main St, Austin, TX 78701-1234", True),
        ("5 George St, Sydney NSW 2000", True),
        #
        # and its look-alikes: no postal code after a space or comma
        #
        ("1234 Main St", False),
        ("Springfield, IL", False),
        ("62704", False),
        ("41.9486, -87.6553", False),
        ("(212) 555-0148", False),
        ("2026-11-18", False),
        ("Akua Mansa", False),
    ],
)
def test_macie_column_shapes_postcode_screen(cell: str, holds: bool) -> None:
    assert _shapes([cell]).may_hold_postcodes() is holds


def test_macie_column_shapes_bad_input() -> None:
    with pytest.raises(ValueError):
        ColumnShapes(column=0, column_name="x")
    with pytest.raises(TypeError):
        ColumnShapes(column=1, column_name=3)
    s = ColumnShapes(column=1, column_name=None)
    with pytest.raises(TypeError):
        s.add(cell=None)
    with pytest.raises(ValueError):
        s.top(n=0)
