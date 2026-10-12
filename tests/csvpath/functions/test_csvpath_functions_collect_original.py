"""collect_original() (#341).

Copies the registered data file the run started from into the run's results
as the well-known file original.<ext>, byte for byte, once per run. It is the
registered file in every source mode: with source-mode: preceding it is still
the registered file, not the preceding csvpath's data.csv. data.csv is
unchanged. original.<ext> is fingerprinted and counted in the manifest.
"""

import contextlib
import io
import json
import os

import pytest

from csvpath import CsvPath
from csvpath.matching.util.exceptions import ChildrenException
from csvpath.util.nos import Nos
from csvpath.util.original_file_utility import OriginalFileUtility as orut
from tests.csvpaths.builder import Builder

TEST_CSV = os.path.join("tests", "csvpath", "test_resources", "test.csv")
DOCS = os.path.join("tests", "csvpath", "test_resources", "documents")
GOOD_XML = os.path.join(DOCS, "orders_good.xml")
BAD_XML = os.path.join(DOCS, "orders_bad.xml")
GOOD_JSON = os.path.join(DOCS, "orders_good.json")
XLSX = os.path.join("tests", "csvpaths", "test_resources", "test.xlsx")
NAME = "collect_original_test"

XML_RULES_NO_NOCONTRIB = """
    not( xpath("/orders/order") ) -> print("There must be at least one order", fail())
    xpath("/orders/order[not(sku)]") -> print("Every order must have a sku", fail())
    xpath("/orders/order[@id = preceding-sibling::order/@id]") -> print("Order ids must be unique", fail())
    collect_original()
    stop()
"""


def _bytes(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


@pytest.fixture
def run_group():
    made = []

    def run(*, file: str, csvpaths: list[str], method: str = "collect_paths"):
        paths = Builder().build()
        paths.config.set(
            section="errors", name="csvpaths", value="print, no-raise, fail, collect"
        )
        paths.paths_manager.remove_named_paths(NAME)
        paths.paths_manager.add_named_paths(name=NAME, paths=csvpaths)
        paths.file_manager.remove_named_file(NAME)
        paths.file_manager.add_named_file(name=NAME, path=file)
        made.append(paths)
        with contextlib.redirect_stdout(io.StringIO()):
            ref = getattr(paths, method)(pathsname=NAME, filename=NAME)
        return paths, paths.results_manager.get_named_results(ref)

    yield run
    for paths in made:
        paths.paths_manager.remove_named_paths(NAME)
        paths.file_manager.remove_named_file(NAME)


def _instance_file(result, name: str) -> str:
    return Nos(result.instance_dir).join(name)


def _manifest(result) -> dict:
    with open(_instance_file(result, "manifest.json"), encoding="utf-8") as f:
        return json.load(f)


#
# the copy
#


def test_collect_original_csv(run_group) -> None:
    _, results = run_group(file=TEST_CSV, csvpaths=["$[1-2][ collect_original() ]"])
    result = results[0]
    copy = _instance_file(result, "original.csv")
    assert _bytes(copy) == _bytes(TEST_CSV)
    #
    # data.csv is unchanged: the two matched lines
    #
    assert len(result.lines.to_list()) == 2


def test_collect_original_json(run_group) -> None:
    _, results = run_group(file=GOOD_JSON, csvpaths=["$[*][ collect_original() ]"])
    assert _bytes(_instance_file(results[0], "original.json")) == _bytes(GOOD_JSON)


def test_collect_original_xlsx(run_group) -> None:
    _, results = run_group(file=XLSX, csvpaths=["$[1][ collect_original() ]"])
    assert _bytes(_instance_file(results[0], "original.xlsx")) == _bytes(XLSX)


#
# rules over a whole document, without .nocontrib
#


def test_collect_original_xml_rules_conforming(run_group) -> None:
    _, results = run_group(
        file=GOOD_XML, csvpaths=[f"$[*][ {XML_RULES_NO_NOCONTRIB} ]"]
    )
    result = results[0]
    assert result.csvpath.is_valid is True
    #
    # the rules found no violation, so the line did not match, but the
    # original is in the results anyway
    #
    assert result.csvpath.match_count == 0
    assert _bytes(_instance_file(result, "original.xml")) == _bytes(GOOD_XML)


def test_collect_original_xml_rules_violating(run_group) -> None:
    _, results = run_group(file=BAD_XML, csvpaths=[f"$[*][ {XML_RULES_NO_NOCONTRIB} ]"])
    result = results[0]
    assert result.csvpath.is_valid is False
    assert _bytes(_instance_file(result, "original.xml")) == _bytes(BAD_XML)


#
# source-mode: preceding
#


def test_collect_original_is_the_registered_file_in_preceding_mode(run_group) -> None:
    first = "~ id: first ~ $[1-2][ yes() ]"
    last = "~ id: last source-mode: preceding ~ $[*][ collect_original() ]"
    _, results = run_group(file=TEST_CSV, csvpaths=[first, last])
    by_id = {r.csvpath.identity: r for r in results}
    preceding_data = _instance_file(by_id["first"], "data.csv")
    last_original = _instance_file(by_id["last"], "original.csv")
    #
    # the last csvpath scanned the preceding data.csv ...
    #
    assert by_id["last"].csvpath.scanner.filename.endswith("data.csv")
    # ... but its original is the registered file
    assert _bytes(last_original) == _bytes(TEST_CSV)
    assert _bytes(last_original) != _bytes(preceding_data)


#
# once per run, and conditional use
#


def test_collect_original_copies_once(run_group, monkeypatch) -> None:
    calls = []
    copy = orut.copy_original

    def counting(*, source, instance_dir):
        calls.append(source)
        return copy(source=source, instance_dir=instance_dir)

    monkeypatch.setattr(orut, "copy_original", staticmethod(counting))
    _, results = run_group(
        file=TEST_CSV, csvpaths=["$[*][ collect_original() collect_original() ]"]
    )
    #
    # one call per collect_original() in the csvpath, not one per line
    #
    assert len(calls) == 2
    assert Nos(_instance_file(results[0], "original.csv")).exists()


def test_collect_original_conditional_on_last_line(run_group) -> None:
    _, results = run_group(
        file=TEST_CSV,
        csvpaths=[
            '$[*][ last.nocontrib() -> collect_original() push("seen", line_number()) ]'
        ],
    )
    assert Nos(_instance_file(results[0], "original.csv")).exists()


def test_collect_original_condition_never_fires(run_group) -> None:
    _, results = run_group(
        file=TEST_CSV, csvpaths=["$[*][ no.nocontrib() -> collect_original() ]"]
    )
    names = Nos(results[0].instance_dir).listdir(files_only=True)
    assert not [n for n in names if n.startswith("original")]


#
# the manifest
#


def test_collect_original_fingerprinted_and_counted(run_group) -> None:
    paths, results = run_group(file=TEST_CSV, csvpaths=["$[*][ collect_original() ]"])
    manifest = _manifest(results[0])
    assert "original.csv" in manifest["file_fingerprints"]
    #
    # the copy has the registered file's fingerprint
    #
    assert manifest["file_fingerprints"]["original.csv"] == (
        paths.file_manager.get_fingerprint_for_name(NAME)
    )


def test_collect_original_counted_in_files_generated(run_group) -> None:
    _, with_original = run_group(file=TEST_CSV, csvpaths=["$[*][ collect_original() ]"])
    n_with = _manifest(with_original[0])["number_of_files_generated"]
    _, without = run_group(file=TEST_CSV, csvpaths=["$[*][ yes() ]"])
    n_without = _manifest(without[0])["number_of_files_generated"]
    assert n_with == n_without + 1


#
# no CsvPaths, no arguments
#


def test_collect_original_bare_csvpath_does_nothing() -> None:
    path = CsvPath()
    with contextlib.redirect_stdout(io.StringIO()):
        path.parse(
            f"~ validation-mode: print, no-raise, fail, collect ~ ${TEST_CSV}[*][ collect_original() ]"
        )
        lines = path.collect()
    assert path.errors_count == 0
    assert path.is_valid is True
    #
    # [*] includes the header line
    #
    assert len(lines) == 9


def test_collect_original_takes_no_arguments() -> None:
    path = CsvPath()
    with pytest.raises(ChildrenException):
        with contextlib.redirect_stdout(io.StringIO()):
            path.parse(
                f"~ validation-mode: print, raise ~ ${TEST_CSV}[*][ collect_original(#firstname) ]"
            )
            path.collect()


#
# OriginalFileUtility
#


@pytest.mark.parametrize(
    "source,expected",
    [
        ("a/b/orders.csv", "original.csv"),
        ("orders.XLSX", "original.xlsx"),
        ("s3://bucket/a/orders.xlsx#Sheet1", "original.xlsx"),
        ("a/b/8b24ab.json", "original.json"),
        ("a/b/noext", "original"),
        ("a\\b\\orders.xml", "original.xml"),
    ],
)
def test_orut_file_name(source: str, expected: str) -> None:
    assert orut.file_name(source) == expected


def test_orut_source_path_strips_sheet() -> None:
    assert orut.source_path("a/orders.xlsx#Sheet1") == "a/orders.xlsx"
    assert orut.source_path("a/orders.csv") == "a/orders.csv"


@pytest.mark.parametrize("bad", [None, "", "  "])
def test_orut_bad_args(bad) -> None:
    with pytest.raises(ValueError):
        orut.source_path(bad)
    with pytest.raises(ValueError):
        orut.copy_original(source="a.csv", instance_dir=bad)


def test_orut_copy_original(tmp_path) -> None:
    dest = orut.copy_original(source=TEST_CSV, instance_dir=str(tmp_path))
    assert dest.endswith("original.csv")
    assert _bytes(dest) == _bytes(TEST_CSV)
