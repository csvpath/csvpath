"""ReferenceSource is the seam between the v3 finders and the metadata
they select from. FilesystemReferenceSource must return exactly what the
managers and files return, because the finders used to call those
directly. Its SQL counterpart (step 4b/4c) will be held to the same
results.

One registered named-file, one two-statement named-paths group and one
run, all under a module-scoped tmp dir.
"""

import pytest

from csvpath import CsvPaths
from csvpath.references.reference_finder_factory_3 import ReferenceFinderFactory3
from csvpath.references.sources.filesystem_reference_source import (
    FilesystemReferenceSource,
)
from csvpath.references.sources.reference_source import ReferenceSource
from csvpath.util.nos import Nos

GROUP = """~ id: first ~ $[*][yes()]

---- CSVPATH ----

~ id: second ~ $[*][yes()]"""


@pytest.fixture(scope="module")
def paths(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("reference_source")
    p = CsvPaths()
    p.config.add_to_config(section="inputs", key="files", value=str(tmp / "named_files"))
    p.config.add_to_config(
        section="inputs", key="csvpaths", value=str(tmp / "named_paths")
    )
    p.config.add_to_config(section="results", key="archive", value=str(tmp / "archive"))
    p.config.add_to_config(section="listeners", key="groups", value="default")
    data = tmp / "orders.csv"
    data.write_text("id,amount\n1,10\n2,20\n", encoding="utf-8")
    group = tmp / "orders.csvpaths"
    group.write_text(GROUP, encoding="utf-8")
    p.file_manager.add_named_file(name="orders", path=str(data))
    p.paths_manager.add_named_paths_from_file(name="orders", file_path=str(group))
    p.collect_paths(pathsname="orders", filename="orders")
    return p


@pytest.fixture(scope="module")
def source(paths):
    return FilesystemReferenceSource(csvpaths=paths)


@pytest.fixture(scope="module")
def run_dir(source):
    homes = source.run_homes(root_major="orders", name_filter=None)
    assert len(homes) == 1
    return homes[0][0]


# ===================
# construction and argument checks
# ===================


def test_is_a_reference_source(source):
    assert isinstance(source, ReferenceSource)


def test_csvpaths_cannot_be_none():
    with pytest.raises(ValueError):
        FilesystemReferenceSource(csvpaths=None)


@pytest.mark.parametrize(
    "method",
    ["file_manifest", "paths_manifest", "run_manifest", "instance_manifest", "instance_dirs"],
)
@pytest.mark.parametrize("bad", [None, "", "  "])
def test_bad_names_raise_value_error(source, method, bad):
    with pytest.raises(ValueError):
        getattr(source, method)(bad)


@pytest.mark.parametrize(
    "method",
    ["file_manifest", "paths_manifest", "run_manifest", "instance_manifest", "instance_dirs"],
)
def test_non_str_names_raise_type_error(source, method):
    with pytest.raises(TypeError):
        getattr(source, method)(3)


def test_read_json_rejects_an_empty_path():
    with pytest.raises(ValueError):
        FilesystemReferenceSource.read_json("")


def test_read_json_missing_file_is_none_and_not_created(tmp_path):
    path = str(tmp_path / "manifest.json")
    assert FilesystemReferenceSource.read_json(path) is None
    assert not Nos(path).exists()


# ===================
# FILES
# ===================


def test_file_manifest(paths, source):
    m = source.file_manifest("orders")
    assert m == paths.file_manager.get_manifest("orders")
    assert len(m) == 1


def test_files_ledger(paths, source):
    ledger = source.files_ledger()
    assert ledger == paths.file_manager.files_root_manifest
    assert [e["named_file_name"] for e in ledger] == ["orders"]


def test_file_names(paths, source):
    assert source.file_names() == paths.file_manager.named_file_names
    assert source.file_names() == ["orders"]


# ===================
# CSVPATHS
# ===================


def test_paths_manifest(paths, source):
    m = source.paths_manifest("orders")
    assert m == paths.paths_manager.get_manifest_for_name("orders")
    assert len(m) == 1


def test_paths_ledger(paths, source):
    assert source.paths_ledger() == paths.paths_manager.paths_root_manifest


def test_paths_names(paths, source):
    assert source.paths_names() == paths.paths_manager.named_paths_names
    assert source.paths_names() == ["orders"]


# ===================
# RESULTS
# ===================


def test_results_ledger(paths, source):
    assert source.results_ledger() == paths.results_manager.results_root_manifest


def test_run_homes_by_group(source, run_dir):
    assert source.run_homes(root_major="orders", name_filter=None) == [
        (run_dir, "orders")
    ]
    assert Nos(run_dir).dir_exists()


def test_run_homes_unknown_group_is_empty(source):
    assert source.run_homes(root_major="nope", name_filter=None) == []


def test_run_homes_every_group_and_by_pattern(source, run_dir):
    assert source.run_homes(root_major=None, name_filter=None) == [
        (run_dir, "orders")
    ]
    assert source.run_homes(root_major=None, name_filter="^ord") == [
        (run_dir, "orders")
    ]
    assert source.run_homes(root_major=None, name_filter="^x") == []


def test_run_manifest(source, run_dir):
    m = source.run_manifest(run_dir)
    assert m == FilesystemReferenceSource.read_json(Nos(run_dir).join("manifest.json"))
    assert m["named_paths_name"] == "orders"


def test_run_manifest_missing_is_none(source, tmp_path):
    assert source.run_manifest(str(tmp_path)) is None


def test_instance_dirs(source, run_dir):
    assert sorted(source.instance_dirs(run_dir)) == ["first", "second"]


def test_instance_manifest(source, run_dir):
    inst = Nos(run_dir).join("second")
    m = source.instance_manifest(inst)
    assert m == FilesystemReferenceSource.read_json(Nos(inst).join("manifest.json"))
    assert int(m["instance_index"]) == 1


def test_instance_manifest_missing_is_none(source, tmp_path):
    assert source.instance_manifest(str(tmp_path)) is None


# ===================
# the finders use a source
# ===================


@pytest.mark.parametrize(
    "reference",
    [
        "$orders.files.:last()",
        "$orders.csvpaths.:last()",
        "$orders.results.:last()",
    ],
)
def test_finder_source_is_filesystem_and_built_once(paths, reference):
    finder = ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=paths)
    s = finder.source
    assert isinstance(s, FilesystemReferenceSource)
    assert s.csvpaths is paths
    assert finder.source is s


@pytest.mark.parametrize(
    "reference",
    [
        "$orders.files.:last()",
        "$orders.csvpaths.:last()",
        "$orders.results.:last()",
    ],
)
def test_finder_resolves_through_its_source(paths, reference):
    #
    # a finder whose source cannot read anything finds nothing: there is
    # no path from the finder to the metadata except through the source
    #
    class _Empty(FilesystemReferenceSource):
        def file_manifest(self, name):
            return []

        def paths_manifest(self, name):
            return []

        def run_homes(self, *, root_major, name_filter):
            return []

    finder = ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=paths)
    assert len(finder.query().results) == 1
    finder = ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=paths)
    finder._source = _Empty(csvpaths=paths)
    assert len(finder.query().results) == 0
