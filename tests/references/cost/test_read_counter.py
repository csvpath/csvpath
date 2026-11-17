import os

import pytest

import csvpath.util.file_readers as file_readers
from csvpath import CsvPaths
from csvpath.references.reference_finder_factory_3 import ReferenceFinderFactory3
from csvpath.util.nos import Nos
from tests.references.cost.read_counter import ReadCounter

#
# The read counter is the oracle the cost estimator is tested against
# (references_v3_cost_estimates.md). These tests pin its classification and
# what the corpus's references really read today, on the local backend.
#
ROOTS = {"archive": "/a/archive", "files": "/a/named_files", "csvpaths": "/a/named_paths"}
RUN = "/a/archive/validate_orders/2026-08-14_19-17-06"


def _counter() -> ReadCounter:
    return ReadCounter(**ROOTS)


@pytest.mark.parametrize(
    "path, kind",
    [
        ("/a/archive/manifest.json", "ledger"),
        ("/a/named_files/manifest.json", "ledger"),
        ("/a/named_paths/manifest.json", "ledger"),
        ("/a/named_files/orders/manifest.json", "named_file_manifest"),
        ("/a/named_files/orders/definition.json", "definition"),
        ("/a/named_files/orders/README.md", "readme"),
        ("/a/named_files/orders/orders.csv/abc.csv", "version_file"),
        ("/a/named_paths/acme/manifest.json", "group_manifest"),
        ("/a/named_paths/acme/group.csvpaths", "version_file"),
        (f"{RUN}/manifest.json", "run_manifest"),
        (f"{RUN}/orders/manifest.json", "instance_manifest"),
        (f"{RUN}/orders/errors.json", "errors_json"),
        (f"{RUN}/orders/vars.json", "vars_json"),
        (f"{RUN}/orders/meta.json", "meta_json"),
        (f"{RUN}/orders/data.csv", "data_file"),
        ("/a/archive/validate_orders/2026-08-14_19-17-06_1/manifest.json", "run_manifest"),
        ("/somewhere/config.ini", None),
    ],
)
def test_a_read_is_classified_by_its_path(path, kind):
    assert _counter().read_kind(path) == kind


@pytest.mark.parametrize(
    "path, kind",
    [
        ("/a/named_files", "name_listing"),
        ("/a/named_paths", "name_listing"),
        (RUN, "run_listing"),
        ("/a/archive/validate_orders", "other_listing"),
        ("/elsewhere", None),
    ],
)
def test_a_listing_is_classified_by_its_path(path, kind):
    assert _counter().listing_kind(path) == kind


def test_the_roots_are_required():
    with pytest.raises(ValueError):
        ReadCounter(archive="", files="/f", csvpaths="/c")


def test_it_restores_what_it_patched():
    listdir, exists = Nos.listdir, Nos.exists
    had_open = hasattr(file_readers, "open")
    with _counter():
        assert Nos.listdir is not listdir
    assert Nos.listdir is listdir and Nos.exists is exists
    assert hasattr(file_readers, "open") == had_open


#
# measured on the corpus (tests/corpus/data: 4 named-files, 3 named-paths
# groups, 11 runs, 23 instances)
#
CORPUS_CONFIG = os.path.join(os.path.dirname(__file__), "..", "..", "corpus", "config", "config.ini")


@pytest.fixture(scope="module")
def csvpaths():
    previous = os.environ.get("CSVPATH_CONFIG_PATH")
    os.environ["CSVPATH_CONFIG_PATH"] = os.path.abspath(CORPUS_CONFIG)
    try:
        yield CsvPaths()
    finally:
        if previous is None:
            os.environ.pop("CSVPATH_CONFIG_PATH", None)
        else:
            os.environ["CSVPATH_CONFIG_PATH"] = previous


def _measure(csvpaths, reference):
    finder = ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=csvpaths)
    with ReadCounter.for_csvpaths(csvpaths) as query:
        selection = finder.query()
    with ReadCounter.for_csvpaths(csvpaths) as resolve:
        finder.resolve_from(selection)
    return dict(query.reads), dict(resolve.reads)


@pytest.mark.parametrize(
    "reference, query_reads, resolve_reads",
    [
        (
            '$*.files.:type("csv")',
            {"name_listing": 1, "named_file_manifest": 4},
            {},
        ),
        (
            "$validate_orders.results.:last().*",
            {"ledger": 1, "run_listing": 1, "instance_manifest": 4},
            {},
        ),
        (
            "$*.results.:all().*:valid(:true())",
            {"ledger": 1, "run_listing": 11, "instance_manifest": 23},
            {},
        ),
        (
            '$validate_orders.results.:flatten().*:errors():idchain("add[0]")',
            {"ledger": 1, "run_listing": 6, "instance_manifest": 16},
            {"errors_json": 16},
        ),
        (
            '$validate_orders.results.:having(:errors(:idchain("add[0]")))',
            {"ledger": 1, "run_listing": 6, "instance_manifest": 16, "errors_json": 16},
            {},
        ),
    ],
)
def test_the_corpus_reads_what_the_spec_models(csvpaths, reference, query_reads, resolve_reads):
    assert _measure(csvpaths, reference) == (query_reads, resolve_reads)
