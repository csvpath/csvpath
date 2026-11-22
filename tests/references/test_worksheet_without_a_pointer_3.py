#
# a '#worksheet' marker with no version pointer (name_one gap review, item
# H). NRE '$acme.files.orders/:name("west coast.xlsx")#march': "the
# reference result returned on query() is the typical path+uuid plus the
# name_two value". A file home has a path and no uuid, and resolves to None
# (5.21 "name_one, no pointer"); with the marker each file home carries the
# worksheet as its identity. It raised "requires a version-selecting
# pointer". A pointer in name_three reads the sheet, as before.
#
# A file home with no workbook version has no worksheets and does not match
# (David, 2026-11-22, decision log D40 d). These tests used CSV file homes
# until then; they now use a small fixture of workbooks beside a CSV (a
# workbook is known by its extension, as resolve knows it).
#
import os

import pytest

from csvpath import CsvPaths
from csvpath.references.reference_exceptions_3 import ReferenceException3
from csvpath.references.reference_finder_factory_3 import ReferenceFinderFactory3
from tests.references.cost.test_results_estimate_soundness_3 import (
    _measure,
    _problems,
)
from tests.references.test_files_wildcard_paths_3 import _config_file

# (file name, versions) under orders/
BOOKS = [("west coast.xlsx", 2), ("east.xlsx", 1), ("plain.csv", 1)]


@pytest.fixture(scope="module")
def books(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("worksheet_without_a_pointer")
    previous = os.environ.get("CSVPATH_CONFIG_PATH")
    os.environ["CSVPATH_CONFIG_PATH"] = _config_file(tmp)
    try:
        p = CsvPaths()
        n = 0
        for filename, versions in BOOKS:
            for v in range(versions):
                src = tmp / "src" / str(n)
                src.mkdir(parents=True)
                (src / filename).write_bytes(f"id\n{n}\n".encode())
                p.file_manager.add_named_file(
                    name="acme", path=str(src / filename), template="orders/:filename"
                )
                n += 1
        yield p
    finally:
        if previous is None:
            os.environ.pop("CSVPATH_CONFIG_PATH", None)
        else:
            os.environ["CSVPATH_CONFIG_PATH"] = previous


def _rows(*, p, reference: str) -> list:
    finder = ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=p)
    return [(str(r.path), r.uuid, r.identity) for r in finder.query().results]


@pytest.mark.parametrize(
    "plain",
    [
        '$acme.files.orders/:name("west coast.xlsx")',
        '$acme.files.orders/:name("east.xlsx")',
        "$acme.files.orders/*",
        "$acme.files.:all()/*",
    ],
)
def test_the_workbook_file_homes_with_the_worksheet_as_identity(books, plain):
    without = [r for r in _rows(p=books, reference=plain) if r[0].endswith(".xlsx")]
    with_marker = _rows(p=books, reference=plain + "#march")
    assert without and [(path, uuid) for path, uuid, _ in with_marker] == [
        (path, uuid) for path, uuid, _ in without
    ]
    assert {identity for _, _, identity in with_marker} == {"march"}
    assert all(uuid is None for _, uuid, _ in with_marker)


def test_a_csv_file_home_among_them_does_not_match(books):
    # D40 d: no worksheet in a CSV file
    paths = [
        os.path.basename(r[0])
        for r in _rows(p=books, reference="$acme.files.orders/*#march")
    ]
    assert "plain.csv" not in paths and sorted(paths) == [
        "east.xlsx",
        "west coast.xlsx",
    ]


def test_resolve_is_none_as_for_a_file_home(books):
    finder = ReferenceFinderFactory3.for_reference(
        reference='$acme.files.orders/:name("west coast.xlsx")#march', csvpaths=books
    )
    assert [r.data for r in finder.resolve_from(finder.query()).results] == [None]


def test_a_pointer_still_selects_a_version(books):
    rows = _rows(
        p=books, reference='$acme.files.orders/:name("west coast.xlsx")#march.:last()'
    )
    assert len(rows) == 1 and rows[0][1] is not None and rows[0][2] == "march"
    assert rows[0][0].endswith(".xlsx")


def test_a_name_three_without_a_pointer_still_raises(books):
    # no example asks for several versions with a worksheet
    finder = ReferenceFinderFactory3.for_reference(
        reference='$acme.files.orders/:name("west coast.xlsx")#march.:from(0)',
        csvpaths=books,
    )
    with pytest.raises(ReferenceException3, match="version-selecting pointer"):
        finder.query()


@pytest.mark.parametrize(
    "reference",
    [
        '$acme.files.orders/:name("west coast.xlsx")#march',
        "$acme.files.orders/*#march",
        '$acme.files.orders/:name("plain.csv")#march',
    ],
)
def test_the_estimate_keeps_its_contract(books, reference):
    finder = ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=books)
    measured, raised = _measure(books, reference)
    assert _problems(finder.estimate(), measured, raised) == []
