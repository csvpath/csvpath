#
# a '#worksheet' (name_two) on a file that has no worksheets, such as a CSV
# file, does not match: nothing is returned and a warning is logged, rather
# than a raise (David, 2026-11-22, decision log D40 d). It was accepted
# quietly with no pointer (the file home came back with the worksheet as
# identity) and raised at resolve with one.
#
import os

import pytest

from csvpath import CsvPaths
from csvpath.references.reference_finder_factory_3 import ReferenceFinderFactory3
from tests.references.cost.test_results_estimate_soundness_3 import (
    _measure,
    _problems,
)
from tests.references.test_files_wildcard_paths_3 import _config_file


@pytest.fixture(scope="module")
def mixed(tmp_path_factory):
    # 'mixed' holds orders.csv and book.xlsx (only the name matters here:
    # the workbook test is the extension, as resolve's is)
    tmp = tmp_path_factory.mktemp("worksheet_on_a_csv")
    previous = os.environ.get("CSVPATH_CONFIG_PATH")
    os.environ["CSVPATH_CONFIG_PATH"] = _config_file(tmp)
    try:
        p = CsvPaths()
        for n, filename in enumerate(("orders.csv", "book.xlsx")):
            src = tmp / "src" / str(n)
            src.mkdir(parents=True)
            (src / filename).write_bytes(b"id\n1\n")
            p.file_manager.add_named_file(name="mixed", path=str(src / filename))
        yield p
    finally:
        if previous is None:
            os.environ.pop("CSVPATH_CONFIG_PATH", None)
        else:
            os.environ["CSVPATH_CONFIG_PATH"] = previous


class _Warnings:
    def __init__(self, logger):
        self.logger = logger
        self.messages = []

    def warning(self, msg, *args, **kwargs):
        self.messages.append(str(msg))

    def __getattr__(self, name):
        return getattr(self.logger, name)


def _query(p, reference: str) -> tuple:
    finder = ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=p)
    seen = _Warnings(finder.csvpaths.logger)
    finder.csvpaths.logger = seen
    try:
        selection = finder.query()
        resolved = finder.resolve_from(selection).results if selection.results else []
    finally:
        finder.csvpaths.logger = seen.logger
    return selection.results, resolved, seen.messages


@pytest.mark.parametrize(
    "reference",
    [
        '$mixed.files.:name("orders.csv")#sheet1',
        '$mixed.files.:name("orders.csv")#sheet1.:last()',
        '$mixed.files.:name("orders.csv")#sheet1.:first()',
    ],
)
def test_a_csv_with_a_worksheet_matches_nothing_and_warns(mixed, reference):
    results, resolved, warnings = _query(mixed, reference)
    assert results == [] and resolved == []
    assert (
        len(warnings) == 1 and "sheet1" in warnings[0] and "orders.csv" in warnings[0]
    )


def test_a_workbook_with_a_worksheet_still_matches(mixed):
    results, _, warnings = _query(mixed, '$mixed.files.:name("book.xlsx")#sheet1')
    assert [os.path.basename(str(r.path)) for r in results] == ["book.xlsx"]
    assert results[0].identity == "sheet1"
    assert warnings == []


def test_a_workbook_version_with_a_worksheet_is_selected(mixed):
    finder = ReferenceFinderFactory3.for_reference(
        reference='$mixed.files.:name("book.xlsx")#sheet1.:last()', csvpaths=mixed
    )
    results = finder.query().results
    assert len(results) == 1 and str(results[0].path).endswith(".xlsx")


def test_no_worksheet_no_change(mixed):
    results, _, warnings = _query(mixed, '$mixed.files.:name("orders.csv").:last()')
    assert len(results) == 1 and warnings == []


@pytest.mark.parametrize(
    "reference",
    [
        '$mixed.files.:name("orders.csv")#sheet1',
        '$mixed.files.:name("orders.csv")#sheet1.:last()',
    ],
)
def test_the_estimate_keeps_its_contract(mixed, reference):
    measured, raised = _measure(mixed, reference)
    assert raised is None
    finder = ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=mixed)
    assert _problems(finder.estimate(), measured, raised) == []


def test_a_csv_named_file_home_with_a_workbook_version_matches():
    # a file home's name is its logical name: 'one.csv' can hold an .xlsx
    # version, so file homes are judged by their versions, not their names
    from tests.references.test_files_reference_finder_3 import ALPHA_HOME, _finder

    manifest = [
        {
            "file": f"{ALPHA_HOME}/one.csv/a1.csv",
            "file_home": f"{ALPHA_HOME}/one.csv",
            "uuid": "u-1",
        },
        {
            "file": f"{ALPHA_HOME}/one.csv/a2.xlsx",
            "file_home": f"{ALPHA_HOME}/one.csv",
            "uuid": "u-2",
        },
    ]
    results = (
        _finder('$alpha.files.:name("one.csv")#sheet1', ALPHA_HOME, manifest)
        .query()
        .results
    )
    assert [(r.uuid, r.identity) for r in results] == [(None, "sheet1")]
    # with a pointer, the selected version's own file decides
    last = (
        _finder('$alpha.files.:name("one.csv")#sheet1.:last()', ALPHA_HOME, manifest)
        .query()
        .results
    )
    first = (
        _finder('$alpha.files.:name("one.csv")#sheet1.:first()', ALPHA_HOME, manifest)
        .query()
        .results
    )
    assert [r.uuid for r in last] == ["u-2"] and first == []
