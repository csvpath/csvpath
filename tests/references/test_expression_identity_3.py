#
# INTERSECT and SUBTRACT compare a result's identity -- a CSVPATHS statement
# ('.first_id') or a FILES worksheet ('#a') -- as UNION's dedupe does
# (ReferenceResult3.__eq__, compendium 7.7). A statement or worksheet shares
# its version's path and uuid, so comparing path+uuid alone made
# '$acme.csvpaths.:last().first_id INTERSECT $acme.csvpaths.:last().second_id'
# keep first_id, and SUBTRACT give []. David, 2026-11-22: fix before release.
#
import os

import pytest

from csvpath import CsvPaths
from csvpath.references.reference_expression_3 import ReferenceExpression3
from tests.references.test_files_wildcard_paths_3 import _config_file

SEP = "\n\n---- CSVPATH ----\n\n"


@pytest.fixture(scope="module")
def archive(tmp_path_factory):
    """a named-paths group 'acme' with statements first_id and second_id,
    and a named-file 'books' with one version of book.xlsx. Paths sides
    are only queried, so the workbook is one by its name, as D39 judges
    it; its bytes are never read."""
    tmp = tmp_path_factory.mktemp("expression_identity")
    previous = os.environ.get("CSVPATH_CONFIG_PATH")
    os.environ["CSVPATH_CONFIG_PATH"] = _config_file(tmp)
    try:
        p = CsvPaths()
        src = tmp / "src"
        src.mkdir()
        group = src / "acme.csvpaths"
        group.write_text(
            SEP.join(["~ id: first_id ~ $[*][yes()]", "~ id: second_id ~ $[*][no()]"]),
            encoding="utf-8",
        )
        p.paths_manager.add_named_paths_from_file(name="acme", file_path=str(group))
        book = src / "book.xlsx"
        book.write_bytes(b"queried only")
        p.file_manager.add_named_file(name="books", path=str(book))
        yield p
    finally:
        if previous is None:
            os.environ.pop("CSVPATH_CONFIG_PATH", None)
        else:
            os.environ["CSVPATH_CONFIG_PATH"] = previous


def _identities(p, expression: str) -> list:
    results = ReferenceExpression3.from_string(expression=expression, csvpaths=p)
    return [r.identity for r in results.resolve().results]


FIRST = "$acme.csvpaths.:last().first_id"
SECOND = "$acme.csvpaths.:last().second_id"
EVERY = "$acme.csvpaths.:last().:all()"
VERSION = "$acme.csvpaths.:last()"
SHEET_A = '$books.files.:name("book.xlsx")#a.:last()'
SHEET_B = '$books.files.:name("book.xlsx")#b.:last()'
WORKBOOK = '$books.files.:name("book.xlsx").:last()'
SHEET_A_UUID = '$books.files.:name("book.xlsx")#a.:last():uuid()'


@pytest.mark.parametrize(
    "expression,identities",
    [
        # two statements of one version
        (f"{FIRST} INTERSECT {SECOND}", []),
        (f"{FIRST} SUBTRACT {SECOND}", ["first_id"]),
        (f"{FIRST} INTERSECT {FIRST}", ["first_id"]),
        (f"{FIRST} SUBTRACT {FIRST}", []),
        # every statement, narrowed to one or less one
        (f"{EVERY} INTERSECT {SECOND}", ["second_id"]),
        (f"{EVERY} SUBTRACT {SECOND}", ["first_id"]),
        # two worksheets of one version
        (f"{SHEET_A} INTERSECT {SHEET_B}", []),
        (f"{SHEET_A} SUBTRACT {SHEET_B}", ["a"]),
        (f"{SHEET_A} INTERSECT {SHEET_A}", ["a"]),
        # a whole version is not one of its parts, as UNION keeps both
        (f"{VERSION} INTERSECT {FIRST}", []),
        (f"{VERSION} SUBTRACT {FIRST}", [None]),
        (f"{SHEET_A} INTERSECT {WORKBOOK}", []),
        (f"{VERSION} INTERSECT {VERSION}", [None]),
    ],
)
def test_intersect_and_subtract_compare_identity(archive, expression, identities):
    assert _identities(archive, expression) == identities


@pytest.mark.parametrize(
    "expression,identities",
    [
        (f"{FIRST} UNION {SECOND}", ["first_id", "second_id"]),
        (f"{SHEET_A} UNION {SHEET_B}", ["a", "b"]),
        (f"{VERSION} UNION {FIRST}", [None, "first_id"]),
    ],
)
def test_union_already_did(archive, expression, identities):
    # unchanged: the consistency INTERSECT and SUBTRACT now share
    assert _identities(archive, expression) == identities


def test_intersect_and_subtract_partition_the_left_side(archive):
    # each left item lands in exactly one of the two
    left = _identities(archive, f"{EVERY} UNION {SHEET_A}")
    kept = _identities(archive, f"({EVERY} UNION {SHEET_A}) INTERSECT {SECOND}")
    dropped = _identities(archive, f"({EVERY} UNION {SHEET_A}) SUBTRACT {SECOND}")
    assert sorted(kept + dropped, key=str) == sorted(left, key=str)
    assert kept == ["second_id"]


@pytest.mark.parametrize(
    "expression,identities",
    [
        # values(LHS)/paths(RHS): the left side's own path, uuid and identity
        (f"{SHEET_A_UUID} INTERSECT {SHEET_B}", []),
        (f"{SHEET_A_UUID} SUBTRACT {SHEET_B}", ["a"]),
        (f"{SHEET_A_UUID} INTERSECT {SHEET_A}", ["a"]),
        # a :having() side is version-level (identity None), so it is not a
        # statement of that version; name the statement on it to match
        (f'{FIRST} INTERSECT $acme.csvpaths.:having("first_id"):last()', []),
        (
            f'{FIRST} INTERSECT $acme.csvpaths.:having("first_id"):last().first_id',
            ["first_id"],
        ),
        # paths(LHS)/values(RHS) with a uuid-valued right side compares the
        # left side's uuid with the value: a statement matches its version's
        # uuid. A uuid value on the left is a version-level item.
        (f"{FIRST} INTERSECT {VERSION}:uuid()", ["first_id"]),
        (f"{VERSION}:uuid() INTERSECT {FIRST}", []),
    ],
)
def test_the_other_comparisons(archive, expression, identities):
    assert _identities(archive, expression) == identities
