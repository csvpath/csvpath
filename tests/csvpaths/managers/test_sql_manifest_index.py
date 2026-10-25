"""manifest_index: an entry's position in its own named-file or
named-paths manifest. FileRegistrar and PathsRegistrar set it on the
metadata right after they append, and the SQL listeners store it, so SQL
can give the JSON manifest order exactly (order by manifest_index) where
`at` can tie.

RESULTS has no manifest_index: run and instance manifests are single
dicts, not appended lists. Runs order by their run-dir names and
instances by instance_index, which instance_run already has.

Also: indexes on the columns the SQL reference source scopes and joins
on, and the updates that add the column and indexes to an existing
database.

Every test uses its own SQLite file and roots under pytest's tmp_path.
The engine is cached in Box, so each test clears it before and after.
"""

import json

import pytest
from sqlalchemy import Column, MetaData, Table, inspect, text

from csvpath import CsvPaths
from csvpath.managers.files.file_metadata import FileMetadata
from csvpath.managers.integrations.sql.references_sql_check import (
    ReferencesSqlCheck,
)
from csvpath.managers.integrations.sql.sql_file_listener import SqlFileListener
from csvpath.managers.integrations.sql.sql_paths_listener import SqlPathsListener
from csvpath.managers.integrations.sql.tables import Tables
from csvpath.managers.integrations.sql.updates import Updates
from csvpath.managers.metadata import Metadata
from csvpath.managers.paths.paths_metadata import PathsMetadata
from csvpath.util.box import Box

UUID_1 = "11111111-1111-4111-8111-111111111111"
UUID_2 = "22222222-2222-4222-8222-222222222222"

INDEXES = {
    "named_file": {
        "ix_named_file_files_root": ["files_root"],
        "ix_named_file_named_file_name": ["named_file_name"],
    },
    "named_paths": {
        "ix_named_paths_paths_root": ["paths_root"],
        "ix_named_paths_paths_name": ["paths_name"],
    },
    "named_paths_group_run": {
        "ix_named_paths_group_run_named_paths_name": ["named_paths_name"],
        "ix_named_paths_group_run_run_home": ["run_home"],
    },
    "instance_run": {
        "ix_instance_run_group_run_uuid": ["group_run_uuid"],
    },
}


def _clear_engine() -> None:
    box = Box()
    e = box.get(key=Box.SQL_ENGINE)
    if e is not None:
        e.dispose()
        box.remove(Box.SQL_ENGINE)


@pytest.fixture
def paths(tmp_path):
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
    p.config.add_to_config(section="sql", key="dialect", value="sqlite")
    p.config.add_to_config(
        section="sql",
        key="connection_string",
        value=f"sqlite:///{tmp_path / 'index.db'}",
    )
    yield p
    _clear_engine()


def _listener(cls, paths: CsvPaths):
    listener = cls(config=paths.config)
    listener.csvpaths = paths
    return listener


def _engine(paths: CsvPaths):
    return _listener(SqlFileListener, paths).engine


def _rows(paths: CsvPaths, *, sql: str) -> list[dict]:
    with _engine(paths).connect() as conn:
        return [dict(r._mapping) for r in conn.execute(text(sql))]


def _indexes(engine, *, table: str) -> dict[str, list[str]]:
    return {i["name"]: i["column_names"] for i in inspect(engine).get_indexes(table)}


def _register_file(paths: CsvPaths, tmp_path, *, n: int) -> None:
    #
    # different content each time, so each registration is a new entry
    #
    data = tmp_path / f"orders_{n}.csv"
    data.write_text(f"id,amount\n{n},10\n", encoding="utf-8")
    paths.file_manager.add_named_file(name="orders", path=str(data))


def _load_paths(paths: CsvPaths, tmp_path, *, statement: str) -> None:
    f = tmp_path / "orders.csvpaths"
    f.write_text(statement, encoding="utf-8")
    paths.paths_manager.add_named_paths_from_file(name="orders", file_path=str(f))


def _old_database(paths: CsvPaths) -> None:
    #
    # the tables as they were before manifest_index: same columns minus
    # manifest_index, and no indexes
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
            if c.name != "manifest_index"
        ]
        Table(t.name, old, *cols)
    old.create_all(_engine(paths))


# ===================
# metadata
# ===================


@pytest.mark.parametrize("cls", [Metadata, FileMetadata, PathsMetadata])
def test_manifest_index_defaults_to_none(paths, cls):
    assert cls(paths.config).manifest_index is None


# ===================
# registrars
# ===================


def test_file_registrar_sets_the_position_of_each_append(paths, tmp_path):
    seen = []
    registrar = paths.file_manager.registrar
    original = registrar.metadata_update

    def spy(mdata):
        original(mdata)
        seen.append(mdata.manifest_index)

    registrar.metadata_update = spy
    for n in range(3):
        _register_file(paths, tmp_path, n=n)
    assert seen == [0, 1, 2]
    assert len(paths.file_manager.get_manifest("orders")) == 3


def test_paths_registrar_sets_the_position_only_when_it_appends(paths, tmp_path):
    seen = []
    registrar = paths.paths_manager.registrar
    original = registrar.metadata_update

    def spy(mdata):
        original(mdata)
        seen.append(mdata.manifest_index)

    registrar.metadata_update = spy
    _load_paths(paths, tmp_path, statement="$[*][yes()]")
    #
    # unchanged fingerprint: no append, so no index
    #
    _load_paths(paths, tmp_path, statement="$[*][yes()]")
    _load_paths(paths, tmp_path, statement="$[*][no()]")
    assert seen == [0, None, 1]
    assert len(paths.paths_manager.get_manifest_for_name("orders")) == 2


# ===================
# SQL listeners
# ===================


def _file_mdata(paths: CsvPaths, *, index: int | None) -> FileMetadata:
    m = FileMetadata(paths.config)
    m.uuid_string = UUID_1
    m.named_file_name = "orders"
    m.origin_path = "data/orders.csv"
    m.name_home = "inputs/named_files/orders"
    m.file_home = "inputs/named_files/orders/orders.csv"
    m.file_path = "inputs/named_files/orders/orders.csv/fp1.csv"
    m.file_name = "orders.csv"
    m.type = "csv"
    m.manifest_path = "inputs/named_files/orders/manifest.json"
    m.manifest_entry = {"uuid": UUID_1}
    m.manifest_index = index
    return m


def _paths_mdata(paths: CsvPaths, *, index: int | None) -> PathsMetadata:
    m = PathsMetadata(paths.config)
    m.uuid_string = UUID_2
    m.named_paths_name = "checks"
    m.named_paths_home = "inputs/named_paths/checks"
    m.group_file_path = "inputs/named_paths/checks/group.csvpaths"
    m.named_paths_count = 1
    m.manifest_path = "inputs/named_paths/checks/manifest.json"
    m.manifest_entry = {"uuid": UUID_2}
    m.manifest_index = index
    return m


@pytest.mark.parametrize(
    "cls,build,table",
    [
        (SqlFileListener, _file_mdata, "named_file"),
        (SqlPathsListener, _paths_mdata, "named_paths"),
    ],
)
@pytest.mark.parametrize("index", [0, 4, None])
def test_listener_stores_the_index(paths, cls, build, table, index):
    _listener(cls, paths).metadata_update(build(paths, index=index))
    rows = _rows(paths, sql=f"select manifest_index from {table}")
    assert rows == [{"manifest_index": index}]


@pytest.mark.parametrize(
    "cls,build,table",
    [
        (SqlFileListener, _file_mdata, "named_file"),
        (SqlPathsListener, _paths_mdata, "named_paths"),
    ],
)
def test_listener_upsert_updates_the_index(paths, cls, build, table):
    listener = _listener(cls, paths)
    listener.metadata_update(build(paths, index=0))
    listener.metadata_update(build(paths, index=3))
    rows = _rows(paths, sql=f"select manifest_index from {table}")
    assert rows == [{"manifest_index": 3}]


# ===================
# end to end: SQL order equals JSON order
# ===================


def test_named_file_rows_in_index_order_match_the_manifest(paths, tmp_path):
    for n in range(3):
        _register_file(paths, tmp_path, n=n)
    manifest = paths.file_manager.get_manifest("orders")
    rows = _rows(
        paths,
        sql="select uuid, manifest_index, manifest_entry from named_file "
        "where named_file_name = 'orders' order by manifest_index",
    )
    assert [r["uuid"] for r in rows] == [e["uuid"] for e in manifest]
    assert [r["manifest_index"] for r in rows] == [0, 1, 2]
    assert [json.loads(r["manifest_entry"]) for r in rows] == manifest


def test_named_paths_rows_in_index_order_match_the_manifest(paths, tmp_path):
    _load_paths(paths, tmp_path, statement="$[*][yes()]")
    _load_paths(paths, tmp_path, statement="$[*][yes()]")
    _load_paths(paths, tmp_path, statement="$[*][no()]")
    manifest = paths.paths_manager.get_manifest_for_name("orders")
    rows = _rows(
        paths,
        sql="select uuid, manifest_index from named_paths "
        "where paths_name = 'orders' order by manifest_index",
    )
    assert [r["uuid"] for r in rows] == [e["uuid"] for e in manifest]
    assert [r["manifest_index"] for r in rows] == [0, 1]


# ===================
# schema: new and existing databases
# ===================


def test_new_database_has_the_column_and_indexes(paths):
    engine = _engine(paths)
    Tables(paths.config, engine=engine).assure_tables()
    insp = inspect(engine)
    for table in ["named_file", "named_paths"]:
        cols = {c["name"]: c for c in insp.get_columns(table)}
        assert "manifest_index" in cols, table
        assert cols["manifest_index"]["nullable"] is True
    for table, expected in INDEXES.items():
        assert _indexes(engine, table=table) == expected, table


def test_updates_add_the_column_and_indexes_to_an_old_database(paths):
    _old_database(paths)
    engine = _engine(paths)
    Updates(engine).do_updates()
    insp = inspect(engine)
    for table in ["named_file", "named_paths"]:
        assert "manifest_index" in [c["name"] for c in insp.get_columns(table)]
    for table, expected in INDEXES.items():
        assert _indexes(engine, table=table) == expected, table


def test_updates_can_run_twice(paths):
    engine = _engine(paths)
    Tables(paths.config, engine=engine).assure_tables()
    Updates(engine).do_updates()
    Updates(engine).do_updates()
    for table, expected in INDEXES.items():
        assert _indexes(engine, table=table) == expected, table


def test_first_write_to_an_old_database_updates_it(paths, tmp_path):
    #
    # the listeners run the updates when an insert fails, as with
    # manifest_entry; the unknown manifest_index column fails the first one
    #
    _old_database(paths)
    _register_file(paths, tmp_path, n=0)
    rows = _rows(paths, sql="select manifest_index from named_file")
    assert rows == [{"manifest_index": 0}]
    assert _indexes(_engine(paths), table="named_file") == INDEXES["named_file"]


def test_check_updates_an_old_database(paths):
    _old_database(paths)
    assert ReferencesSqlCheck.problems(csvpaths=paths) == []


def test_check_reports_what_the_updates_could_not_fix(paths, monkeypatch):
    _old_database(paths)
    monkeypatch.setattr(Updates, "do_updates", lambda self: None)
    problems = ReferencesSqlCheck.problems(csvpaths=paths)
    for table in ["named_file", "named_paths"]:
        assert f"table {table} has no manifest_index column" in problems
    for table, expected in INDEXES.items():
        for name in expected:
            assert f"table {table} has no index {name}" in problems
    assert "table instance_run has no manifest_index column" not in problems
