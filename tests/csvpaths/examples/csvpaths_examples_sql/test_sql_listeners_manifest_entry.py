"""The SQL listeners store the exact manifest entry the primary registrar
wrote (mdata.manifest_entry) in each table's manifest_entry column, and
write nothing when the registrar wrote nothing.

Also covers two small corrections made alongside:
  - SqlPathsListener's upsert set paths_root to the paths name
  - ResultMetadata.named_paths_uuid held the group run's uuid at instance
    start; the group run uuid now has its own field, group_run_uuid

Every test uses its own SQLite file under pytest's tmp_path. The engine is
cached in Box, so each test clears it before and after.
"""

import json
import os

import pytest
from sqlalchemy import Column, MetaData, Table, inspect, text

from csvpath import CsvPaths
from csvpath.managers.files.file_metadata import FileMetadata
from csvpath.managers.listener import Listener
from csvpath.managers.integrations.sql.sql_file_listener import SqlFileListener
from csvpath.managers.integrations.sql.sql_paths_listener import SqlPathsListener
from csvpath.managers.integrations.sql.sql_result_listener import SqlResultListener
from csvpath.managers.integrations.sql.sql_results_listener import (
    SqlResultsListener,
)
from csvpath.managers.integrations.sql.tables import Tables
from csvpath.managers.paths.paths_metadata import PathsMetadata
from csvpath.managers.results.result_metadata import ResultMetadata
from csvpath.managers.results.results_metadata import ResultsMetadata
from csvpath.util.box import Box

UUID_1 = "11111111-1111-4111-8111-111111111111"
UUID_2 = "22222222-2222-4222-8222-222222222222"
UUID_3 = "33333333-3333-4333-8333-333333333333"
UUID_4 = "44444444-4444-4444-8444-444444444444"

TABLES = ["named_file", "named_paths", "instance_run", "named_paths_group_run"]


def _clear_engine() -> None:
    box = Box()
    e = box.get(key=Box.SQL_ENGINE)
    if e is not None:
        e.dispose()
        box.remove(Box.SQL_ENGINE)


def _use_sqlite(paths: CsvPaths, *, db_path: str) -> None:
    paths.config.add_to_config(section="sql", key="dialect", value="sqlite")
    paths.config.add_to_config(
        section="sql", key="connection_string", value=f"sqlite:///{db_path}"
    )


@pytest.fixture
def paths(tmp_path):
    _clear_engine()
    p = CsvPaths()
    _use_sqlite(p, db_path=str(tmp_path / "listeners.db"))
    yield p
    _clear_engine()


def _listener(cls, paths: CsvPaths):
    listener = cls(config=paths.config)
    listener.csvpaths = paths
    return listener


def _rows(paths: CsvPaths, *, table: str) -> list[dict]:
    listener = _listener(SqlFileListener, paths)
    with listener.engine.connect() as conn:
        result = conn.execute(text(f"select * from {table}"))
        return [dict(r._mapping) for r in result]


def _columns(paths: CsvPaths, *, table: str) -> list[str]:
    listener = _listener(SqlFileListener, paths)
    return [c["name"] for c in inspect(listener.engine).get_columns(table)]


# ===================
# metadata builders
# ===================


def _file_mdata(paths: CsvPaths, *, entry: dict | None) -> FileMetadata:
    m = FileMetadata(paths.config)
    m.uuid_string = UUID_1
    m.named_file_name = "orders"
    m.origin_path = "data/orders.csv"
    m.name_home = "inputs/named_files/orders"
    m.file_home = "inputs/named_files/orders/orders.csv"
    m.file_path = "inputs/named_files/orders/orders.csv/fp1.csv"
    m.file_name = "fp1.csv"
    m.type = "csv"
    m.manifest_path = "inputs/named_files/orders/manifest.json"
    m.manifest_entry = entry
    return m


def _paths_mdata(paths: CsvPaths, *, entry: dict | None) -> PathsMetadata:
    m = PathsMetadata(paths.config)
    m.uuid_string = UUID_2
    m.named_paths_name = "checks"
    m.named_paths_home = "inputs/named_paths/checks"
    m.group_file_path = "inputs/named_paths/checks/group.csvpaths"
    m.named_paths_count = 1
    m.manifest_path = "inputs/named_paths/checks/manifest.json"
    m.manifest_entry = entry
    return m


def _result_mdata(paths: CsvPaths, *, entry: dict | None) -> ResultMetadata:
    m = ResultMetadata(paths.config)
    m.uuid_string = UUID_3
    m.group_run_uuid_string = UUID_4
    m.instance_identity = "one"
    m.instance_home = "archive/checks/2026-01-01_00-00-00/one"
    m.manifest_path = "archive/checks/2026-01-01_00-00-00/one/manifest.json"
    m.manifest_entry = entry
    return m


def _results_mdata(paths: CsvPaths, *, entry: dict | None) -> ResultsMetadata:
    m = ResultsMetadata(paths.config)
    m.uuid_string = UUID_4
    m.status = "started"
    m.run_home = "archive/checks/2026-01-01_00-00-00"
    m.named_paths_uuid_string = UUID_2
    m.named_paths_name = "checks"
    m.named_file_uuid_string = UUID_1
    m.named_file_name = "orders"
    m.named_file_path = "inputs/named_files/orders/orders.csv/fp1.csv"
    m.manifest_path = "archive/checks/2026-01-01_00-00-00/manifest.json"
    m.manifest_entry = entry
    return m


# (listener class, metadata builder, table)
CASES = [
    (SqlFileListener, _file_mdata, "named_file"),
    (SqlPathsListener, _paths_mdata, "named_paths"),
    (SqlResultListener, _result_mdata, "instance_run"),
    (SqlResultsListener, _results_mdata, "named_paths_group_run"),
]
CASE_IDS = [c[2] for c in CASES]


# ===================
# schema
# ===================


def test_every_table_defines_a_nullable_manifest_entry_column(paths):
    tables = Tables(paths.config)
    for t in [
        tables.named_file,
        tables.named_paths,
        tables.instance_run,
        tables.group_run,
    ]:
        assert "manifest_entry" in t.c, t.name
        assert t.c.manifest_entry.nullable is True, t.name


def test_assured_tables_have_the_manifest_entry_column(paths):
    _listener(SqlFileListener, paths).tables
    for table in TABLES:
        assert "manifest_entry" in _columns(paths, table=table), table


# ===================
# each listener
# ===================


@pytest.mark.parametrize("cls,build,table", CASES, ids=CASE_IDS)
def test_listener_stores_the_manifest_entry_as_json(paths, cls, build, table):
    entry = {"uuid": "x", "nested": {"a": [1, 2]}, "flag": True}
    _listener(cls, paths).metadata_update(build(paths, entry=entry))
    rows = _rows(paths, table=table)
    assert len(rows) == 1
    assert json.loads(rows[0]["manifest_entry"]) == entry


@pytest.mark.parametrize("cls,build,table", CASES, ids=CASE_IDS)
def test_listener_writes_nothing_without_a_manifest_entry(paths, cls, build, table):
    listener = _listener(cls, paths)
    #
    # tables are created on first use; create them so there is a table
    # to find empty
    #
    listener.tables
    listener.metadata_update(build(paths, entry=None))
    assert _rows(paths, table=table) == []


@pytest.mark.parametrize("cls,build,table", CASES, ids=CASE_IDS)
def test_second_update_for_the_same_uuid_replaces_the_entry(paths, cls, build, table):
    #
    # the run and instance rows are upserted at start and again at
    # completion; the row must end with the completion-time entry
    #
    listener = _listener(cls, paths)
    listener.metadata_update(build(paths, entry={"status": "started"}))
    listener.metadata_update(build(paths, entry={"status": "complete"}))
    rows = _rows(paths, table=table)
    assert len(rows) == 1
    assert json.loads(rows[0]["manifest_entry"]) == {"status": "complete"}


# ===================
# existing databases
# ===================


def _create_old_schema(paths: CsvPaths) -> None:
    #
    # the four tables as they were before manifest_entry
    #
    current = Tables(paths.config)
    old = MetaData()
    for t in [
        current.group_run,
        current.instance_run,
        current.named_file,
        current.named_paths,
    ]:
        cols = [
            Column(c.name, c.type, primary_key=c.primary_key, nullable=c.nullable)
            for c in t.columns
            if c.name != "manifest_entry"
        ]
        Table(t.name, old, *cols)
    old.create_all(_listener(SqlFileListener, paths).engine)


@pytest.mark.parametrize("cls,build,table", CASES, ids=CASE_IDS)
def test_listener_adds_the_column_to_an_existing_database(paths, cls, build, table):
    _create_old_schema(paths)
    assert "manifest_entry" not in _columns(paths, table=table)
    entry = {"uuid": "x"}
    _listener(cls, paths).metadata_update(build(paths, entry=entry))
    assert "manifest_entry" in _columns(paths, table=table)
    rows = _rows(paths, table=table)
    assert len(rows) == 1
    assert json.loads(rows[0]["manifest_entry"]) == entry


# ===================
# SqlPathsListener paths_root
# ===================


def test_paths_upsert_sets_paths_root_not_paths_name(paths):
    listener = _listener(SqlPathsListener, paths)
    listener.metadata_update(_paths_mdata(paths, entry={"v": 1}))
    #
    # the second update conflicts on uuid, so the row is set from _set()
    #
    mdata = _paths_mdata(paths, entry={"v": 2})
    mdata.named_paths_root = "some/other/root"
    listener.metadata_update(mdata)
    rows = _rows(paths, table="named_paths")
    assert len(rows) == 1
    assert rows[0]["paths_root"] == "some/other/root"
    assert rows[0]["paths_name"] == "checks"


def test_instance_row_uses_group_run_uuid(paths):
    _listener(SqlResultListener, paths).metadata_update(
        _result_mdata(paths, entry={"v": 1})
    )
    assert _rows(paths, table="instance_run")[0]["group_run_uuid"] == UUID_4


# ===================
# ResultMetadata.group_run_uuid
# ===================


class TestResultMetadataGroupRunUuid:
    def test_defaults_to_none(self, paths):
        m = ResultMetadata(paths.config)
        assert m.group_run_uuid is None
        assert m.group_run_uuid_string is None

    def test_string_round_trip(self, paths):
        m = ResultMetadata(paths.config)
        m.group_run_uuid_string = UUID_4
        assert m.group_run_uuid_string == UUID_4
        assert str(m.group_run_uuid) == UUID_4

    def test_separate_from_named_paths_uuid(self, paths):
        m = ResultMetadata(paths.config)
        m.group_run_uuid_string = UUID_4
        m.named_paths_uuid_string = UUID_2
        assert m.group_run_uuid_string == UUID_4
        assert m.named_paths_uuid_string == UUID_2

    def test_string_setter_rejects_none(self, paths):
        with pytest.raises(ValueError):
            ResultMetadata(paths.config).group_run_uuid_string = None

    def test_string_setter_rejects_non_string(self, paths):
        with pytest.raises(ValueError):
            ResultMetadata(paths.config).group_run_uuid_string = 5

    def test_setter_rejects_non_uuid(self, paths):
        with pytest.raises(ValueError):
            ResultMetadata(paths.config).group_run_uuid = UUID_4


# ===================
# end to end
# ===================


class _CaptureResultListener(Listener):
    """records the uuids each result update carries, at start and at
    completion, as the other listeners see them"""

    def __init__(self, config) -> None:
        super().__init__(config)
        self.seen: list[tuple[str, str]] = []

    def metadata_update(self, mdata) -> None:
        self.seen.append(
            (
                mdata.named_paths_uuid_string,
                getattr(mdata, "group_run_uuid_string", None),
            )
        )


@pytest.fixture
def run_paths(tmp_path):
    #
    # a CsvPaths whose inputs, archive and database are all under tmp_path,
    # with the default and sql listeners on
    #
    _clear_engine()
    p = CsvPaths()
    p.config.add_to_config(
        section="inputs", key="files", value=str(tmp_path / "named_files")
    )
    p.config.add_to_config(
        section="inputs", key="csvpaths", value=str(tmp_path / "named_paths")
    )
    p.config.add_to_config(
        section="results", key="archive", value=str(tmp_path / "archive")
    )
    p.config.add_to_config(section="listeners", key="groups", value="default, sql")
    _use_sqlite(p, db_path=str(tmp_path / "run.db"))
    data = tmp_path / "orders.csv"
    data.write_text("id,amount\n1,10\n2,20\n", encoding="utf-8")
    p.file_manager.add_named_file(name="orders", path=str(data))
    p.paths_manager.add_named_paths(
        name="checks",
        paths=["$[*][~ id: one ~ yes()]", "$[*][~ id: two ~ gt(#amount, 15)]"],
    )
    capture = _CaptureResultListener(p.config)
    p.results_manager.dynamic_result_listeners.append(capture)
    p.collect_paths(pathsname="checks", filename="orders")
    p.capture = capture
    yield p
    _clear_engine()


def _read_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _entries(rows: list[dict]) -> list[dict]:
    return [json.loads(r["manifest_entry"]) for r in rows]


def test_run_rows_carry_the_manifests_written_to_disk(run_paths):
    p = run_paths
    files_mani = p.file_manager.get_manifest("orders")
    assert _entries(_rows(p, table="named_file")) == files_mani

    paths_mani = p.paths_manager.get_manifest_for_name("checks")
    assert _entries(_rows(p, table="named_paths")) == paths_mani

    run_rows = _rows(p, table="named_paths_group_run")
    assert len(run_rows) == 1
    run_mani = _read_json(os.path.join(run_rows[0]["run_home"], "manifest.json"))
    assert _entries(run_rows) == [run_mani]

    instance_rows = _rows(p, table="instance_run")
    assert len(instance_rows) == 2
    for row in instance_rows:
        assert json.loads(row["manifest_entry"]) == _read_json(row["manifest_path"])


def test_run_uuids_join_and_mean_what_they_say(run_paths):
    p = run_paths
    np_uuid = _rows(p, table="named_paths")[0]["uuid"]
    run_row = _rows(p, table="named_paths_group_run")[0]
    assert run_row["named_paths_uuid"] == np_uuid
    for row in _rows(p, table="instance_run"):
        assert row["group_run_uuid"] == run_row["uuid"]
        instance_mani = _read_json(row["manifest_path"])
        assert instance_mani["named_paths_uuid"] == np_uuid
    #
    # two instances, each updated at start and at completion. every update
    # carries the named-paths uuid and the group run uuid in their own
    # fields, not the group run uuid in named_paths_uuid at start
    #
    assert p.capture.seen == [(np_uuid, run_row["uuid"])] * 4


def test_reloading_an_unchanged_group_writes_no_sql_row(run_paths):
    p = run_paths
    before = _rows(p, table="named_paths")
    assert len(before) == 1
    p.paths_manager.add_named_paths(
        name="checks",
        paths=["$[*][~ id: one ~ yes()]", "$[*][~ id: two ~ gt(#amount, 15)]"],
    )
    assert len(p.paths_manager.get_manifest_for_name("checks")) == 1
    assert _rows(p, table="named_paths") == before
