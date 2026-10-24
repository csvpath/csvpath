"""Low-level tests for each primary registrar's create_json_from(mdata) and
for metadata_update() recording the written entry on mdata.manifest_entry.

create_json_from() is the single place a manifest entry is built; listeners
that mirror manifests (e.g. the SQL listeners) rely on mdata.manifest_entry
being exactly what was written. Expected dicts are compared as item lists so
key order -- and so the JSON written to disk -- is pinned too.
"""

import json

import pytest

from csvpath.managers.files.file_metadata import FileMetadata
from csvpath.managers.files.file_registrar import FileRegistrar
from csvpath.managers.metadata import Metadata
from csvpath.managers.paths.paths_metadata import PathsMetadata
from csvpath.managers.paths.paths_registrar import PathsRegistrar
from csvpath.managers.results.result_metadata import ResultMetadata
from csvpath.managers.results.result_registrar import ResultRegistrar
from csvpath.managers.results.results_metadata import ResultsMetadata
from csvpath.managers.results.results_registrar import ResultsRegistrar
from tests.csvpaths.builder import Builder

TIME = "2026-01-02T03:04:05+00:00"
TIME_STARTED = "2026-01-02T03:04:06+00:00"
TIME_COMPLETED = "2026-01-02T03:04:07+00:00"
UUID_1 = "11111111-1111-4111-8111-111111111111"
UUID_2 = "22222222-2222-4222-8222-222222222222"
UUID_3 = "33333333-3333-4333-8333-333333333333"
UUID_4 = "44444444-4444-4444-8444-444444444444"


@pytest.fixture(scope="module")
def csvpaths():
    return Builder().build()


def _read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


class _StubResult:
    def __init__(self, run_dir: str) -> None:
        self.run_dir = run_dir
        self.identity_or_index = "inst"


class _StubSerializer:
    def __init__(self, instance_dir: str) -> None:
        self.instance_dir = instance_dir

    def get_instance_dir(self, *, run_dir: str, identity: str) -> str:
        return self.instance_dir


def test_metadata_manifest_entry_defaults_to_none(csvpaths):
    assert Metadata(csvpaths.config).manifest_entry is None


# ===================
# PathsRegistrar
# ===================


def _paths_mdata(csvpaths, *, manifest_path: str, full: bool) -> PathsMetadata:
    m = PathsMetadata(csvpaths.config)
    m.time_string = TIME
    m.uuid_string = UUID_1
    m.archive_name = "archive"
    m.named_paths_name = "orders"
    m.named_paths_home = "inputs/named_paths/orders"
    m.group_file_path = "inputs/named_paths/orders/group.csvpaths"
    m.named_paths = ["$[*][yes()]"]
    m.named_paths_identities = ["one"]
    m.named_paths_count = 1
    m.fingerprint = "fp1"
    m.manifest_path = manifest_path
    if full:
        m.source_path = "src/orders.csvpaths"
        m.time_started_string = TIME_STARTED
        m.time_completed_string = TIME_COMPLETED
        m.template = ":1/:run_dir"
    return m


class TestPathsRegistrarCreateJsonFrom:
    def test_full_entry(self, csvpaths):
        reg = PathsRegistrar(csvpaths)
        m = reg.create_json_from(
            _paths_mdata(csvpaths, manifest_path="mp.json", full=True)
        )
        assert list(m.items()) == [
            ("archive_name", "archive"),
            ("named_paths_name", "orders"),
            ("named_paths_home", "inputs/named_paths/orders"),
            ("group_file_path", "inputs/named_paths/orders/group.csvpaths"),
            ("source_path", "src/orders.csvpaths"),
            ("named_paths", ["$[*][yes()]"]),
            ("named_paths_identities", ["one"]),
            ("named_paths_count", 1),
            ("fingerprint", "fp1"),
            ("time", TIME),
            ("time_started", TIME_STARTED),
            ("time_completed", TIME_COMPLETED),
            ("uuid", UUID_1),
            ("manifest_path", "mp.json"),
            ("template", ":1/:run_dir"),
        ]

    def test_optional_keys_absent_when_unset(self, csvpaths):
        reg = PathsRegistrar(csvpaths)
        m = reg.create_json_from(
            _paths_mdata(csvpaths, manifest_path="mp.json", full=False)
        )
        for key in ("source_path", "time_started", "time_completed", "template"):
            assert key not in m

    def test_none_mdata_raises(self, csvpaths):
        with pytest.raises(ValueError):
            PathsRegistrar(csvpaths).create_json_from(None)

    def test_metadata_update_sets_written_entry(self, csvpaths, tmp_path):
        reg = PathsRegistrar(csvpaths)
        mp = str(tmp_path / "manifest.json")
        reg.intermediary.put_json(mp, [])
        mdata = _paths_mdata(csvpaths, manifest_path=mp, full=False)
        reg.metadata_update(mdata)
        written = _read_json(mp)
        assert len(written) == 1
        assert mdata.manifest_entry == written[0]
        assert mdata.manifest_entry == reg.create_json_from(mdata)

    def test_unchanged_fingerprint_leaves_entry_none(self, csvpaths, tmp_path):
        reg = PathsRegistrar(csvpaths)
        mp = str(tmp_path / "manifest.json")
        reg.intermediary.put_json(mp, [])
        reg.metadata_update(_paths_mdata(csvpaths, manifest_path=mp, full=False))
        again = _paths_mdata(csvpaths, manifest_path=mp, full=False)
        reg.metadata_update(again)
        assert again.manifest_entry is None
        assert len(_read_json(mp)) == 1


# ===================
# FileRegistrar
# ===================


def _file_mdata(
    csvpaths, *, manifest_path: str, mark: str | None, template: str | None
) -> FileMetadata:
    m = FileMetadata(csvpaths.config)
    m.time_string = TIME
    m.uuid_string = UUID_1
    m.origin_path = "src/orders.csv"
    m.file_path = "inputs/named_files/orders/orders.csv/fp1.csv"
    m.file_home = "inputs/named_files/orders/orders.csv"
    m.file_name = "orders.csv"
    m.fingerprint = "fp1"
    m.type = "csv"
    m.reference = "$orders.files.fp1"
    m.mark = mark
    m.template = template
    m.username = "user"
    m.hostname = "host"
    m.manifest_path = manifest_path
    return m


class TestFileRegistrarCreateJsonFrom:
    def test_full_entry(self, csvpaths):
        reg = FileRegistrar(csvpaths)
        m = reg.create_json_from(
            _file_mdata(csvpaths, manifest_path="mp.json", mark="0", template=":1")
        )
        assert list(m.items()) == [
            ("type", "csv"),
            ("reference", "$orders.files.fp1"),
            ("file", "inputs/named_files/orders/orders.csv/fp1.csv"),
            ("file_home", "inputs/named_files/orders/orders.csv"),
            ("fingerprint", "fp1"),
            ("uuid", UUID_1),
            ("time", TIME),
            ("from", "src/orders.csv"),
            ("mark", "0"),
            ("template", ":1"),
            ("manifest_path", "mp.json"),
            ("file_name", "orders.csv"),
            ("username", "user"),
            ("hostname", "host"),
        ]

    def test_mark_absent_and_template_defaults_to_empty(self, csvpaths):
        reg = FileRegistrar(csvpaths)
        m = reg.create_json_from(
            _file_mdata(csvpaths, manifest_path="mp.json", mark=None, template=None)
        )
        assert "mark" not in m
        assert m["template"] == ""

    def test_none_mdata_raises(self, csvpaths):
        with pytest.raises(ValueError):
            FileRegistrar(csvpaths).create_json_from(None)

    def test_metadata_update_sets_written_entry(self, csvpaths, tmp_path):
        reg = FileRegistrar(csvpaths)
        mp = str(tmp_path / "manifest.json")
        mdata = _file_mdata(csvpaths, manifest_path=mp, mark=None, template=None)
        reg.metadata_update(mdata)
        written = _read_json(mp)
        assert len(written) == 1
        assert mdata.manifest_entry == written[0]
        assert mdata.manifest_entry == reg.create_json_from(mdata)


# ===================
# ResultsRegistrar
# ===================


def _results_mdata(csvpaths, *, manifest_path: str, completed: bool) -> ResultsMetadata:
    m = ResultsMetadata(csvpaths.config)
    m.time_string = TIME
    m.run_uuid_string = UUID_1
    m.uuid_string = UUID_2
    m.by_line = True
    m.status = "complete" if completed else "start"
    m.run_home = "archive/orders/2026-01-02_03-04-05"
    m.named_results_name = "orders"
    m.named_paths_name = "orders"
    m.named_paths_uuid_string = UUID_3
    m.named_paths_fingerprint = "pfp"
    m.named_file_name = "orders"
    m.named_file_uuid_string = UUID_4
    m.named_file_path = "inputs/named_files/orders/orders.csv/fp1.csv"
    m.named_file_size = 10
    m.named_file_last_change = "lc"
    m.named_file_fingerprint = "ffp"
    m.named_file_fingerprint_on_file = "ffp"
    m.hostname = "host"
    m.username = "user"
    m.ip_address = None
    m.method = "collect_paths"
    m.template = None
    m.manifest_path = manifest_path
    if completed:
        m.time_completed_string = TIME_COMPLETED
        m.all_completed = True
        m.all_valid = True
        m.error_count = 0
        m.all_expected_files = True
    return m


class TestResultsRegistrarCreateJsonFrom:
    def _reg(self, csvpaths, run_dir: str) -> ResultsRegistrar:
        return ResultsRegistrar(csvpaths=csvpaths, run_dir=run_dir, pathsname="orders")

    def test_full_entry(self, csvpaths, tmp_path):
        m = self._reg(csvpaths, str(tmp_path)).create_json_from(
            _results_mdata(csvpaths, manifest_path="mp.json", completed=True)
        )
        assert list(m.items()) == [
            ("time", TIME),
            ("uuid", UUID_2),
            ("run_uuid", UUID_1),
            ("serial", False),
            ("time_completed", TIME_COMPLETED),
            ("all_completed", True),
            ("all_valid", True),
            ("error_count", 0),
            ("all_expected_files", True),
            ("status", "complete"),
            ("run_home", "archive/orders/2026-01-02_03-04-05"),
            ("named_results_name", "orders"),
            ("named_paths_name", "orders"),
            ("named_paths_uuid", UUID_3),
            ("named_paths_fingerprint", "pfp"),
            ("named_file_name", "orders"),
            ("named_file_uuid", UUID_4),
            ("named_file_path", "inputs/named_files/orders/orders.csv/fp1.csv"),
            ("named_file_size", 10),
            ("named_file_last_change", "lc"),
            ("named_file_fingerprint", "ffp"),
            ("named_file_fingerprint_on_file", "ffp"),
            ("hostname", "host"),
            ("username", "user"),
            ("ip_address", None),
            ("method", "collect_paths"),
            ("template", ""),
            ("manifest_path", "mp.json"),
        ]

    def test_completion_keys_absent_at_start(self, csvpaths, tmp_path):
        m = self._reg(csvpaths, str(tmp_path)).create_json_from(
            _results_mdata(csvpaths, manifest_path="mp.json", completed=False)
        )
        for key in (
            "time_completed",
            "all_completed",
            "all_valid",
            "error_count",
            "all_expected_files",
        ):
            assert key not in m

    def test_none_mdata_raises(self, csvpaths, tmp_path):
        with pytest.raises(ValueError):
            self._reg(csvpaths, str(tmp_path)).create_json_from(None)

    def test_metadata_update_sets_written_entry(self, csvpaths, tmp_path):
        reg = self._reg(csvpaths, str(tmp_path))
        mp = str(tmp_path / "manifest.json")
        mdata = _results_mdata(csvpaths, manifest_path=mp, completed=True)
        reg.metadata_update(mdata)
        assert mdata.manifest_entry == _read_json(mp)
        assert mdata.manifest_entry == reg.create_json_from(mdata)


# ===================
# ResultRegistrar
# ===================


def _result_mdata(csvpaths, *, preceding: bool, transfers) -> ResultMetadata:
    m = ResultMetadata(csvpaths.config)
    m.time_string = TIME
    m.uuid_string = UUID_1
    m.by_line = True
    m.archive_name = "archive"
    m.named_results_name = "orders"
    m.named_paths_uuid_string = UUID_3
    m.run = "2026-01-02_03-04-05"
    m.run_uuid_string = UUID_2
    m.run_home = "archive/orders/2026-01-02_03-04-05"
    m.instance_identity = "inst"
    m.instance_index = 0
    m.instance_home = "archive/orders/2026-01-02_03-04-05/inst"
    m.file_fingerprints = {"data.csv": "dfp"}
    m.files_expected = True
    m.number_of_files_expected = 1
    m.number_of_files_generated = 1
    m.valid = True
    m.completed = True
    m.error_count = 0
    m.method = "collect_paths"
    m.source_mode_preceding = preceding
    m.preceding_instance_identity = "prev"
    m.actual_data_file = "inputs/named_files/orders/orders.csv/fp1.csv"
    m.origin_data_file = "inputs/named_files/orders/orders.csv/fp1.csv"
    m.named_file_name = "orders"
    m.transfers = transfers
    return m


class TestResultRegistrarCreateJsonFrom:
    def _reg(self, csvpaths, tmp_path) -> ResultRegistrar:
        return ResultRegistrar(
            csvpaths=csvpaths,
            result=_StubResult(str(tmp_path)),
            result_serializer=_StubSerializer(str(tmp_path / "inst")),
        )

    def test_full_entry(self, csvpaths, tmp_path):
        m = self._reg(csvpaths, tmp_path).create_json_from(
            _result_mdata(csvpaths, preceding=True, transfers=[["data", "t1"]]),
            manifest_path="mp.json",
        )
        assert list(m.items()) == [
            ("time", TIME),
            ("uuid", UUID_1),
            ("serial", False),
            ("archive_name", "archive"),
            ("named_results_name", "orders"),
            ("named_paths_uuid", UUID_3),
            ("run", "2026-01-02_03-04-05"),
            ("run_uuid", UUID_2),
            ("run_home", "archive/orders/2026-01-02_03-04-05"),
            ("instance_identity", "inst"),
            ("instance_index", 0),
            ("instance_home", "archive/orders/2026-01-02_03-04-05/inst"),
            ("file_fingerprints", {"data.csv": "dfp"}),
            ("files_expected", True),
            ("number_of_files_expected", 1),
            ("number_of_files_generated", 1),
            ("valid", True),
            ("completed", True),
            ("error_count", 0),
            ("method", "collect_paths"),
            ("source_mode_preceding", True),
            ("preceding_instance_identity", "prev"),
            ("actual_data_file", "inputs/named_files/orders/orders.csv/fp1.csv"),
            ("origin_data_file", "inputs/named_files/orders/orders.csv/fp1.csv"),
            ("named_file_name", "orders"),
            ("transfers", [["data", "t1"]]),
            ("manifest_path", "mp.json"),
        ]

    def test_optional_keys_absent_when_unset(self, csvpaths, tmp_path):
        m = self._reg(csvpaths, tmp_path).create_json_from(
            _result_mdata(csvpaths, preceding=False, transfers=None),
            manifest_path="mp.json",
        )
        assert "preceding_instance_identity" not in m
        assert "transfers" not in m

    def test_valid_none_becomes_empty_string(self, csvpaths, tmp_path):
        mdata = _result_mdata(csvpaths, preceding=False, transfers=None)
        mdata.valid = None
        m = self._reg(csvpaths, tmp_path).create_json_from(
            mdata, manifest_path="mp.json"
        )
        assert m["valid"] == ""

    def test_none_mdata_raises(self, csvpaths, tmp_path):
        with pytest.raises(ValueError):
            self._reg(csvpaths, tmp_path).create_json_from(
                None, manifest_path="mp.json"
            )

    @pytest.mark.parametrize("bad", [None, "", "  "])
    def test_bad_manifest_path_raises(self, csvpaths, tmp_path, bad):
        with pytest.raises(ValueError):
            self._reg(csvpaths, tmp_path).create_json_from(
                _result_mdata(csvpaths, preceding=False, transfers=None),
                manifest_path=bad,
            )

    def test_none_time_raises(self, csvpaths, tmp_path):
        mdata = _result_mdata(csvpaths, preceding=False, transfers=None)
        mdata._time = None
        with pytest.raises(ValueError):
            self._reg(csvpaths, tmp_path).create_json_from(
                mdata, manifest_path="mp.json"
            )

    def test_create_json_from_does_no_io(self, csvpaths, tmp_path):
        self._reg(csvpaths, tmp_path).create_json_from(
            _result_mdata(csvpaths, preceding=False, transfers=None),
            manifest_path="mp.json",
        )
        assert not (tmp_path / "inst").exists()

    def test_metadata_update_sets_written_entry(self, csvpaths, tmp_path):
        reg = self._reg(csvpaths, tmp_path)
        mdata = _result_mdata(csvpaths, preceding=False, transfers=None)
        reg.metadata_update(mdata)
        mp = str(tmp_path / "inst" / "manifest.json")
        assert mdata.manifest_entry == _read_json(mp)
        assert mdata.manifest_entry["manifest_path"] == mp
        assert mdata.manifest_entry == reg.create_json_from(mdata, manifest_path=mp)
