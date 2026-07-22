import os
import unittest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
from csvpath.util.run_home_maker import RunHomeMaker
from csvpath.util.exceptions import CsvPathsException
from csvpath.util.nos import Nos

TMP_DIR = os.path.join("tests", "util", "test_resources", "tmp", "run_home_maker")


class FakeConfig:
    def __init__(self, archive_path):
        self.archive_path = archive_path


class FakeFileManager:
    def __init__(self, manifest_entries):
        self._manifest_entries = manifest_entries

    def get_manifest(self, name):
        return self._manifest_entries


class FakeCsvPaths:
    def __init__(
        self,
        *,
        archive_path=None,
        manifest_entries=None,
        current_run_time=None,
        run_time_str=None,
    ):
        self.config = FakeConfig(archive_path)
        self.file_manager = FakeFileManager(manifest_entries)
        self._current_run_time = None
        self.current_run_time = current_run_time
        self._run_time_str = run_time_str


class TestUtilRunHomeMakerSimple(unittest.TestCase):
    def test_base_dir_delegates_to_config_archive_path(self):
        csvpaths = FakeCsvPaths(archive_path="/some/archive")
        maker = RunHomeMaker(csvpaths)
        assert maker.base_dir == "/some/archive"

    def test_current_run_time_sets_and_caches_on_csvpaths(self):
        csvpaths = FakeCsvPaths()
        maker = RunHomeMaker(csvpaths)
        assert csvpaths._current_run_time is None
        first = maker.current_run_time
        assert first is not None
        assert csvpaths._current_run_time is first
        second = maker.current_run_time
        assert second is first

    def test_current_run_time_returns_existing_value_without_overwriting(self):
        fixed = datetime(2025, 3, 11, 18, 50, 56, tzinfo=timezone.utc)
        csvpaths = FakeCsvPaths()
        csvpaths._current_run_time = fixed
        maker = RunHomeMaker(csvpaths)
        assert maker.current_run_time is fixed

    def test_deref_paths_name_strips_dollar_sign(self):
        maker = RunHomeMaker(FakeCsvPaths())
        assert maker._deref_paths_name("$myname") == "myname"

    def test_deref_paths_name_truncates_at_dot(self):
        maker = RunHomeMaker(FakeCsvPaths())
        assert maker._deref_paths_name("$myname.files.abc") == "myname"

    def test_deref_paths_name_truncates_at_hash(self):
        maker = RunHomeMaker(FakeCsvPaths())
        assert maker._deref_paths_name("$myname#identity") == "myname"

    def test_deref_paths_name_plain_name_is_unchanged(self):
        maker = RunHomeMaker(FakeCsvPaths())
        assert maker._deref_paths_name("myname") == "myname"

    def test_run_time_str_raises_when_nothing_to_go_on(self):
        csvpaths = FakeCsvPaths(run_time_str=None)
        maker = RunHomeMaker(csvpaths)
        with self.assertRaises(CsvPathsException):
            maker.run_time_str(pathsname=None, filename=None)

    def test_run_time_str_short_circuits_when_already_set(self):
        csvpaths = FakeCsvPaths(run_time_str="already-set")
        maker = RunHomeMaker(csvpaths)
        # pathsname is None but that is fine, because get_run_dir short
        # circuits on _run_time_str before ever touching pathsname
        assert maker.run_time_str(pathsname=None, filename=None) == "already-set"


class TestUtilRunHomeMakerGetDataFilePath(unittest.TestCase):
    def test_plain_name_returns_from_of_last_manifest_entry(self):
        entries = [{"from": "/a/b/c1.csv"}, {"from": "/a/b/c2.csv"}]
        csvpaths = FakeCsvPaths(manifest_entries=entries)
        maker = RunHomeMaker(csvpaths)
        assert maker.get_data_file_path("myfile") == "/a/b/c2.csv"

    def test_plain_name_raises_value_error_when_path_is_none(self):
        entries = [{"from": None}]
        csvpaths = FakeCsvPaths(manifest_entries=entries)
        maker = RunHomeMaker(csvpaths)
        with self.assertRaises(ValueError):
            maker.get_data_file_path("myfile")

    def test_reference_files_datatype_returns_from_of_indexed_version(self):
        with patch(
            "csvpath.util.run_home_maker.ReferenceParser"
        ) as MockRefParser, patch(
            "csvpath.util.run_home_maker.FilesReferenceFinder"
        ) as MockFilesFinder:
            MockRefParser.RESULTS = "results"
            MockRefParser.FILES = "files"
            fake_ref = MagicMock()
            fake_ref.datatype = "files"
            MockRefParser.return_value = fake_ref

            fake_finder = MagicMock()
            fake_finder.manifest = {0: {"from": "/x/y.csv"}, 1: {"from": "/x/z.csv"}}
            fake_finder.version_index = 1
            MockFilesFinder.return_value = fake_finder

            csvpaths = FakeCsvPaths(manifest_entries=[{"from": "ignored"}])
            maker = RunHomeMaker(csvpaths)
            assert maker.get_data_file_path("$myfile.files.v1") == "/x/z.csv"

    def test_reference_results_datatype_with_no_name_three_raises_runtime_error(self):
        # source comment says this branch "cannot work" / "there must be
        # no test and may be no use case" -- confirming the documented
        # RuntimeError does at least fire as written
        with patch("csvpath.util.run_home_maker.ReferenceParser") as MockRefParser:
            MockRefParser.RESULTS = "results"
            MockRefParser.FILES = "files"
            fake_ref = MagicMock()
            fake_ref.datatype = "results"
            fake_ref.name_three = None
            MockRefParser.return_value = fake_ref

            csvpaths = FakeCsvPaths(manifest_entries=[{"from": "ignored"}])
            maker = RunHomeMaker(csvpaths)
            with self.assertRaises(RuntimeError):
                maker.get_data_file_path("$myresults.results")

    def test_reference_results_datatype_with_name_three_reads_origin_data_file(self):
        with patch(
            "csvpath.util.run_home_maker.ReferenceParser"
        ) as MockRefParser, patch(
            "csvpath.util.run_home_maker.ResultsReferenceFinder"
        ) as MockResultsFinder:
            MockRefParser.RESULTS = "results"
            MockRefParser.FILES = "files"
            fake_ref = MagicMock()
            fake_ref.datatype = "results"
            fake_ref.name_three = "abc"
            MockRefParser.return_value = fake_ref

            instance_dir = os.path.join(TMP_DIR, "instance")
            os.makedirs(instance_dir, exist_ok=True)
            manifest_path = os.path.join(instance_dir, "manifest.json")
            with open(manifest_path, "w", encoding="utf-8") as f:
                f.write('{"origin_data_file": "/origin/data.csv"}')

            fake_finder = MagicMock()
            fake_finder.resolve.return_value = [instance_dir]
            MockResultsFinder.return_value = fake_finder

            csvpaths = FakeCsvPaths(manifest_entries=[{"from": "ignored"}])
            maker = RunHomeMaker(csvpaths)
            try:
                path = maker.get_data_file_path("$myresults.results.abc")
                assert path == "/origin/data.csv"
            finally:
                Nos(TMP_DIR).remove()
                os.makedirs(TMP_DIR, exist_ok=True)

    def test_reference_results_datatype_missing_manifest_raises_value_error(
        self,
    ):
        # regression test: in the RESULTS + name_three-is-not-None
        # branch, "path" used to only be assigned inside
        # "if nos.exists():". When the manifest.json was missing, path
        # was never bound, so the method's own
        # "if path is None: raise ValueError(...)" guard at the end never
        # ran -- Python raised UnboundLocalError instead of the intended,
        # friendlier ValueError. Fixed by initializing path = None right
        # before the nos.exists() check.
        with patch(
            "csvpath.util.run_home_maker.ReferenceParser"
        ) as MockRefParser, patch(
            "csvpath.util.run_home_maker.ResultsReferenceFinder"
        ) as MockResultsFinder:
            MockRefParser.RESULTS = "results"
            MockRefParser.FILES = "files"
            fake_ref = MagicMock()
            fake_ref.datatype = "results"
            fake_ref.name_three = "abc"
            MockRefParser.return_value = fake_ref

            # instance_dir exists but has no manifest.json in it
            instance_dir = os.path.join(TMP_DIR, "instance_no_manifest")
            os.makedirs(instance_dir, exist_ok=True)

            fake_finder = MagicMock()
            fake_finder.resolve.return_value = [instance_dir]
            MockResultsFinder.return_value = fake_finder

            csvpaths = FakeCsvPaths(manifest_entries=[{"from": "ignored"}])
            maker = RunHomeMaker(csvpaths)
            try:
                with self.assertRaises(ValueError):
                    maker.get_data_file_path("$myresults.results.abc")
            finally:
                Nos(TMP_DIR).remove()
                os.makedirs(TMP_DIR, exist_ok=True)

    def test_unhandled_reference_datatype_raises_value_error(self):
        with patch("csvpath.util.run_home_maker.ReferenceParser") as MockRefParser:
            MockRefParser.RESULTS = "results"
            MockRefParser.FILES = "files"
            fake_ref = MagicMock()
            fake_ref.datatype = "something-else"
            MockRefParser.return_value = fake_ref

            csvpaths = FakeCsvPaths(manifest_entries=[{"from": "ignored"}])
            maker = RunHomeMaker(csvpaths)
            with self.assertRaises(ValueError):
                maker.get_data_file_path("$mything.something-else")


class TestUtilRunHomeMakerGetRunDir(unittest.TestCase):
    def setUp(self):
        nos = Nos(TMP_DIR)
        if not nos.dir_exists():
            nos.makedirs()

    def tearDown(self):
        nos = Nos(TMP_DIR)
        if nos.dir_exists():
            nos.remove()

    def _csvpaths(self, *, run_time=None, manifest_from="/source/a/b/e.csv"):
        return FakeCsvPaths(
            archive_path=TMP_DIR,
            manifest_entries=[{"from": manifest_from}],
            current_run_time=run_time
            or datetime(2025, 3, 11, 18, 50, 56, tzinfo=timezone.utc),
        )

    def test_short_circuits_when_run_time_str_already_set(self):
        csvpaths = FakeCsvPaths(run_time_str="already-decided")
        maker = RunHomeMaker(csvpaths)
        result = maker.get_run_dir(paths_name="anything", file_name="anything")
        assert result == "already-decided"
        # no filesystem side effects: archive_path was never even set
        assert csvpaths.config.archive_path is None

    def test_plain_names_build_expected_run_dir_and_set_run_time_str(self):
        csvpaths = self._csvpaths()
        maker = RunHomeMaker(csvpaths)
        result = maker.get_run_dir(paths_name="myname", file_name="myfile.csv")
        expected = os.path.join(TMP_DIR, "myname", "2025-03-11_18-50-56")
        assert result == expected
        assert csvpaths._run_time_str == expected
        # the parent (base_dir/paths_name) is created eagerly
        assert Nos(os.path.join(TMP_DIR, "myname")).dir_exists()

    def test_colliding_run_dir_gets_a_numeric_suffix(self):
        csvpaths = self._csvpaths()
        maker = RunHomeMaker(csvpaths)
        taken = os.path.join(TMP_DIR, "myname", "2025-03-11_18-50-56")
        os.makedirs(taken)
        result = maker.get_run_dir(paths_name="myname", file_name="myfile.csv")
        assert result == f"{taken}_0"
        assert Nos(result).dir_exists()

    def test_two_collisions_increment_the_suffix(self):
        csvpaths = self._csvpaths()
        maker = RunHomeMaker(csvpaths)
        base = os.path.join(TMP_DIR, "myname", "2025-03-11_18-50-56")
        os.makedirs(base)
        os.makedirs(f"{base}_0")
        result = maker.get_run_dir(paths_name="myname", file_name="myfile.csv")
        assert result == f"{base}_1"

    def test_reference_paths_name_uses_root_major(self):
        with patch("csvpath.util.run_home_maker.ReferenceParser") as MockRefParser:
            fake_ref = MagicMock()
            fake_ref.root_major = "derefed-name"
            MockRefParser.return_value = fake_ref

            csvpaths = self._csvpaths()
            maker = RunHomeMaker(csvpaths)
            result = maker.get_run_dir(paths_name="$some.reference", file_name="myfile.csv")
            expected = os.path.join(TMP_DIR, "derefed-name", "2025-03-11_18-50-56")
            assert result == expected

    def test_reference_file_name_files_datatype_uses_manifest_entry_from(self):
        with patch(
            "csvpath.util.run_home_maker.ReferenceParser"
        ) as MockRefParser, patch(
            "csvpath.util.run_home_maker.ReferenceManifestEntryFinder"
        ) as MockFinder:
            fake_ref = MagicMock()
            fake_ref.FILES = "files"
            fake_ref.RESULTS = "results"
            fake_ref.datatype = "files"
            MockRefParser.return_value = fake_ref

            fake_finder = MagicMock()
            fake_finder.get_file_manifest_entry_for_reference.return_value = {
                "from": "/source/x/y/z.csv"
            }
            MockFinder.return_value = fake_finder

            csvpaths = self._csvpaths()
            maker = RunHomeMaker(csvpaths)
            result = maker.get_run_dir(paths_name="myname", file_name="$myfile.files")
            expected = os.path.join(TMP_DIR, "myname", "2025-03-11_18-50-56")
            assert result == expected
            fake_finder.get_file_manifest_entry_for_reference.assert_called_once()


if __name__ == "__main__":
    unittest.main()
