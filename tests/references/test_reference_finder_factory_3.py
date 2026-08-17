import pytest

from csvpath.references.csvpaths_reference_finder_3 import CsvpathsReferenceFinder3
from csvpath.references.files_reference_finder_3 import FilesReferenceFinder3
from csvpath.references.reference_finder_factory_3 import ReferenceFinderFactory3
from csvpath.references.results_reference_finder_3 import ResultsReferenceFinder3


class _FakeFileManager:
    def named_file_home(self, name):
        return f"inputs/named_files/{name}"

    def get_manifest(self, name):
        return []

    @property
    def named_file_names(self):
        return []

    @property
    def files_root_manifest(self):
        return []


class _FakePathsManager:
    def get_manifest_for_name(self, name):
        return []

    def named_paths_home(self, name):
        return f"named_paths/{name}"

    @property
    def named_paths_names(self):
        return []

    @property
    def paths_root_manifest(self):
        return []


class _FakeResultsManager:
    def get_named_results_home(self, name):
        return f"archive/{name}"

    @property
    def results_root_manifest(self):
        return []


class _FakeConfig:
    def get(self, section, name):
        return "archive"

    inputs_files_path = None
    inputs_csvpaths_path = None


class _FakeCsvPaths:
    def __init__(self):
        self.file_manager = _FakeFileManager()
        self.paths_manager = _FakePathsManager()
        self.results_manager = _FakeResultsManager()
        self.config = _FakeConfig()


def _csvpaths() -> _FakeCsvPaths:
    return _FakeCsvPaths()


class TestReferenceFinderFactory3:
    def test_files_reference_gives_a_files_finder(self):
        finder = ReferenceFinderFactory3.for_reference(
            reference='$alpha.files.:name("orders.csv").:last()', csvpaths=_csvpaths()
        )
        assert isinstance(finder, FilesReferenceFinder3)

    def test_csvpaths_reference_gives_a_csvpaths_finder(self):
        finder = ReferenceFinderFactory3.for_reference(
            reference="$acme.csvpaths.:last()", csvpaths=_csvpaths()
        )
        assert isinstance(finder, CsvpathsReferenceFinder3)

    def test_results_reference_gives_a_results_finder(self):
        finder = ReferenceFinderFactory3.for_reference(
            reference="$acme.results.:last()", csvpaths=_csvpaths()
        )
        assert isinstance(finder, ResultsReferenceFinder3)

    def test_the_returned_finder_is_actually_usable(self):
        # not just the right class -- constructed correctly enough to
        # run query() without blowing up, given only empty fake
        # manifests.
        finder = ReferenceFinderFactory3.for_reference(
            reference="$acme.csvpaths.:last()", csvpaths=_csvpaths()
        )
        results = finder.query()
        assert results.results == []

    @pytest.mark.parametrize("bad_reference", [None, ""])
    def test_rejects_none_or_empty_reference(self, bad_reference):
        with pytest.raises(ValueError):
            ReferenceFinderFactory3.for_reference(
                reference=bad_reference, csvpaths=_csvpaths()
            )

    def test_rejects_none_csvpaths(self):
        with pytest.raises(ValueError):
            ReferenceFinderFactory3.for_reference(
                reference="$acme.results.:last()", csvpaths=None
            )

    def test_an_unparseable_reference_raises(self):
        # a grammar-level failure (no leading '$') raises straight from
        # the Lark parser, not ReferenceException3 -- confirmed via
        # direct testing; ReferenceParser3 only wraps exceptions raised
        # from INSIDE a transformer rule (e.g. Reference3's own
        # validation), not raw grammar/tokenizing failures.
        with pytest.raises(Exception):
            ReferenceFinderFactory3.for_reference(
                reference="not a reference at all", csvpaths=_csvpaths()
            )
