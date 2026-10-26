"""The SQL mirror of the named-files and named-paths root ledgers
(harmonization PR 2). FilesListener / PathsListener set
mdata.ledger_entry and ledger_index right after they append to their
ledger, and SqlFileListener / SqlPathsListener store that exact entry and
its position in named_file_ledger / named_paths_ledger.

A ledger has entries that are not versions: an unchanged named-paths
reload adds a ledger entry but no manifest entry. The entry is marked
unchanged and names the version it matched, which its ledger row links.

Every test uses its own SQLite file and roots under pytest's tmp_path.
The engine is cached in Box, so each test clears it before and after.
"""

import json
from datetime import datetime

import pytest
from sqlalchemy import Column, MetaData, Table, inspect, text

from csvpath import CsvPaths
from csvpath.managers.files.file_metadata import FileMetadata
from csvpath.managers.files.files_listener import FilesListener
from csvpath.managers.integrations.sql.references_sql_check import (
    ReferencesSqlCheck,
)
from csvpath.managers.integrations.sql.sql_file_listener import SqlFileListener
from csvpath.managers.integrations.sql.sql_listener import SqlListener
from csvpath.managers.integrations.sql.sql_upsert_utility import (
    SqlUpsertUtility as squt,
)
from csvpath.managers.integrations.sql.tables import Tables
from csvpath.managers.integrations.sql.updates import Updates
from csvpath.managers.metadata import Metadata
from csvpath.managers.paths.paths_listener import PathsListener
from csvpath.managers.paths.paths_metadata import PathsMetadata
from csvpath.util.box import Box
from csvpath.util.exceptions import RequiredListenerException

NO_RAISE_POLICY = "collect, print"

LEDGER_TABLES = ["named_file_ledger", "named_paths_ledger"]

LEDGER_COLUMNS = {
    "named_file_ledger": [
        "uuid",
        "at",
        "files_root",
        "named_file_name",
        "ledger_entry",
        "ledger_index",
        "status",
        "lifecycle",
        "version_uuid",
    ],
    "named_paths_ledger": [
        "uuid",
        "at",
        "paths_root",
        "paths_name",
        "ledger_entry",
        "ledger_index",
        "status",
        "lifecycle",
        "version_uuid",
    ],
}

LEDGER_INDEXES = {
    "named_file_ledger": {
        "ix_named_file_ledger_root_index": ["files_root", "ledger_index"],
        "ix_named_file_ledger_root_name": ["files_root", "named_file_name"],
    },
    "named_paths_ledger": {
        "ix_named_paths_ledger_root_index": ["paths_root", "ledger_index"],
        "ix_named_paths_ledger_root_name": ["paths_root", "paths_name"],
    },
}


def _clear_engine() -> None:
    box = Box()
    e = box.get(key=Box.SQL_ENGINE)
    if e is not None:
        e.dispose()
        box.remove(Box.SQL_ENGINE)


def _paths(tmp_path, *, groups: str) -> CsvPaths:
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
    p.config.add_to_config(section="listeners", key="groups", value=groups)
    p.config.add_to_config(section="sql", key="dialect", value="sqlite")
    p.config.add_to_config(
        section="sql",
        key="connection_string",
        value=f"sqlite:///{tmp_path / 'ledger.db'}",
    )
    return p


@pytest.fixture
def paths(tmp_path):
    _clear_engine()
    yield _paths(tmp_path, groups="sql")
    _clear_engine()


@pytest.fixture
def no_sql(tmp_path):
    _clear_engine()
    yield _paths(tmp_path, groups="")
    _clear_engine()


def _engine(paths: CsvPaths):
    listener = SqlFileListener(config=paths.config)
    listener.csvpaths = paths
    return listener.engine


def _rows(paths: CsvPaths, *, sql: str) -> list[dict]:
    with _engine(paths).connect() as conn:
        return [dict(r._mapping) for r in conn.execute(text(sql))]


def _indexes(engine, *, table: str) -> dict[str, list[str]]:
    return {i["name"]: i["column_names"] for i in inspect(engine).get_indexes(table)}


def _register(paths: CsvPaths, tmp_path, *, n: int = 0, name: str = "orders") -> None:
    data = tmp_path / f"{name}_{n}.csv"
    data.write_text(f"id,amount\n{n},10\n", encoding="utf-8")
    paths.file_manager.add_named_file(name=name, path=str(data))


def _load(paths: CsvPaths, tmp_path, *, statement: str = "$[*][yes()]") -> None:
    f = tmp_path / "orders.csvpaths"
    f.write_text(statement, encoding="utf-8")
    paths.paths_manager.add_named_paths_from_file(name="orders", file_path=str(f))


def _files_ledger(paths: CsvPaths) -> list:
    return paths.file_manager.files_root_manifest or []


def _paths_ledger(paths: CsvPaths) -> list:
    return paths.paths_manager.paths_root_manifest or []


def _ledger_rows(paths: CsvPaths, *, table: str) -> list[dict]:
    return _rows(paths, sql=f"select * from {table} order by ledger_index")


class _FailingWrite:
    """a DataFileWriter stand-in whose write fails"""

    def __init__(self, *args, **kwargs) -> None: ...

    def __enter__(self):
        raise OSError("ledger write failed")

    def __exit__(self, *args) -> None: ...


# ===================
# metadata and the ledger writers
# ===================


@pytest.mark.parametrize("cls", [Metadata, FileMetadata, PathsMetadata])
def test_ledger_fields_default_to_none(paths, cls):
    m = cls(paths.config)
    assert m.ledger_entry is None
    assert m.ledger_index is None


def test_files_listener_sets_the_entry_and_position_it_wrote(no_sql, tmp_path):
    seen = []
    original = FilesListener.metadata_update

    def spy(self, mdata):
        original(self, mdata)
        seen.append((mdata.ledger_entry, mdata.ledger_index))

    FilesListener.metadata_update = spy
    try:
        for n in range(3):
            _register(no_sql, tmp_path, n=n)
    finally:
        FilesListener.metadata_update = original
    ledger = _files_ledger(no_sql)
    assert [i for _, i in seen] == [0, 1, 2]
    assert [e for e, _ in seen] == ledger


def test_paths_listener_sets_the_entry_and_position_it_wrote(no_sql, tmp_path):
    seen = []
    original = PathsListener.metadata_update

    def spy(self, mdata):
        original(self, mdata)
        seen.append((mdata.ledger_entry, mdata.ledger_index))

    PathsListener.metadata_update = spy
    try:
        _load(no_sql, tmp_path, statement="$[*][yes()]")
        _load(no_sql, tmp_path, statement="$[*][no()]")
    finally:
        PathsListener.metadata_update = original
    assert [i for _, i in seen] == [0, 1]
    assert [e for e, _ in seen] == _paths_ledger(no_sql)


def test_a_failed_ledger_write_leaves_the_fields_unset(no_sql, monkeypatch):
    monkeypatch.setattr(
        "csvpath.managers.files.files_listener.DataFileWriter", _FailingWrite
    )
    lst = FilesListener(csvpaths=no_sql)
    #
    # manifest_path() creates the ledger with the same writer; make it exist
    #
    monkeypatch.setattr(lst, "manifest_path", lambda: "unused")
    monkeypatch.setattr(lst, "get_manifest", lambda mpath: [])
    mdata = FileMetadata(no_sql.config)
    mdata.named_file_name = "orders"
    with pytest.raises(OSError):
        lst.metadata_update(mdata)
    assert mdata.ledger_entry is None
    assert mdata.ledger_index is None


# ===================
# the mirror
# ===================


def test_files_ledger_rows_equal_the_json_ledger(paths, tmp_path):
    _register(paths, tmp_path, n=0)
    _register(paths, tmp_path, n=1, name="invoices")
    _register(paths, tmp_path, n=2)
    ledger = _files_ledger(paths)
    rows = _ledger_rows(paths, table="named_file_ledger")
    assert len(ledger) == 3
    assert [json.loads(r["ledger_entry"]) for r in rows] == ledger
    assert [r["ledger_index"] for r in rows] == [0, 1, 2]
    assert [r["uuid"] for r in rows] == [e["uuid"] for e in ledger]
    assert [r["named_file_name"] for r in rows] == ["orders", "invoices", "orders"]
    assert {r["files_root"] for r in rows} == {str(tmp_path / "named_files")}


def test_paths_ledger_rows_equal_the_json_ledger(paths, tmp_path):
    _load(paths, tmp_path, statement="$[*][yes()]")
    _load(paths, tmp_path, statement="$[*][no()]")
    ledger = _paths_ledger(paths)
    rows = _ledger_rows(paths, table="named_paths_ledger")
    assert len(ledger) == 2
    assert [json.loads(r["ledger_entry"]) for r in rows] == ledger
    assert [r["ledger_index"] for r in rows] == [0, 1]
    assert [r["paths_name"] for r in rows] == ["orders", "orders"]
    assert {r["paths_root"] for r in rows} == {str(tmp_path / "named_paths")}


def test_an_arrival_links_its_version(paths, tmp_path):
    _register(paths, tmp_path, n=0)
    _load(paths, tmp_path)
    for table in LEDGER_TABLES:
        rows = _ledger_rows(paths, table=table)
        assert len(rows) == 1, table
        assert rows[0]["version_uuid"] == rows[0]["uuid"], table
    versions = _rows(paths, sql="select uuid from named_file")
    assert versions[0]["uuid"] == _ledger_rows(paths, table="named_file_ledger")[0][
        "uuid"
    ]


def test_an_unchanged_reload_has_a_ledger_row_but_no_version(paths, tmp_path):
    _load(paths, tmp_path)
    _load(paths, tmp_path)
    rows = _ledger_rows(paths, table="named_paths_ledger")
    assert len(_paths_ledger(paths)) == 2
    assert [json.loads(r["ledger_entry"]) for r in rows] == _paths_ledger(paths)
    assert rows[0]["version_uuid"] == rows[0]["uuid"]
    #
    # the reload links the version it matched (PR 4)
    #
    assert rows[1]["version_uuid"] == rows[0]["uuid"]
    assert len(_rows(paths, sql="select uuid from named_paths")) == 1


def test_status_and_lifecycle_are_read_from_the_entry(paths, tmp_path):
    _register(paths, tmp_path)
    row = _ledger_rows(paths, table="named_file_ledger")[0]
    assert "status" not in json.loads(row["ledger_entry"])
    assert row["status"] is None
    assert row["lifecycle"] is None


def test_no_ledger_entry_means_no_ledger_row(paths, tmp_path, monkeypatch):
    #
    # a ledger write that failed: the version is still mirrored
    #
    monkeypatch.setattr(FilesListener, "metadata_update", lambda self, mdata: None)
    _register(paths, tmp_path)
    assert _ledger_rows(paths, table="named_file_ledger") == []
    assert len(_rows(paths, sql="select uuid from named_file")) == 1


def test_without_the_sql_group_no_ledger_tables_are_written(no_sql, tmp_path):
    _register(no_sql, tmp_path)
    _load(no_sql, tmp_path)
    assert len(_files_ledger(no_sql)) == 1
    insp = inspect(_engine(no_sql))
    for table in LEDGER_TABLES:
        assert not insp.has_table(table), table


@pytest.mark.parametrize("policy", ["raise, collect, print", NO_RAISE_POLICY])
def test_a_failed_ledger_row_raises_required_under_on(paths, tmp_path, policy):
    paths.config.add_to_config(section="errors", key="csvpaths", value=policy)
    paths.config.add_to_config(section="references", key="sql", value="on")
    original = SqlListener._upsert_ledger_row_unreliably

    def fail(self, *, table, row):
        raise RuntimeError("ledger row failed")

    SqlListener._upsert_ledger_row_unreliably = fail
    try:
        with pytest.raises(RequiredListenerException, match="SqlFileListener"):
            _register(paths, tmp_path)
    finally:
        SqlListener._upsert_ledger_row_unreliably = original
    #
    # the JSON ledger is the source of truth and was written first. then
    # add_named_file's except clause records the failure as well. the
    # failure has its own uuid and links the attempt by registration_uuid
    #
    ledger = _files_ledger(paths)
    assert len(ledger) == 2
    assert "status" not in ledger[0]
    assert ledger[1]["status"] == "Registration failed"
    assert ledger[0]["uuid"] != ledger[1]["uuid"]
    assert ledger[1]["registration_uuid"] == ledger[0]["uuid"]


def test_a_failed_ledger_row_is_logged_under_off_without_raise_policy(
    paths, tmp_path
):
    paths.config.add_to_config(section="errors", key="csvpaths", value=NO_RAISE_POLICY)
    original = SqlListener._upsert_ledger_row_unreliably

    def fail(self, *, table, row):
        raise RuntimeError("ledger row failed")

    SqlListener._upsert_ledger_row_unreliably = fail
    try:
        _register(paths, tmp_path)
    finally:
        SqlListener._upsert_ledger_row_unreliably = original
    assert len(_files_ledger(paths)) == 1
    assert _ledger_rows(paths, table="named_file_ledger") == []


# ===================
# the row builder
# ===================


def _row_args(mdata) -> dict:
    return {
        "mdata": mdata,
        "root_column": "files_root",
        "root": "/r",
        "name_column": "named_file_name",
        "name": "orders",
    }


def test_ledger_row_requires_a_ledger_entry(paths):
    lst = SqlFileListener(config=paths.config)
    with pytest.raises(ValueError):
        lst._ledger_row(**_row_args(None))
    with pytest.raises(ValueError):
        lst._ledger_row(**_row_args(FileMetadata(paths.config)))


@pytest.mark.parametrize("key", ["root_column", "root", "name_column", "name"])
@pytest.mark.parametrize("bad", [None, "", "  ", 3])
def test_ledger_row_rejects_bad_columns(paths, key, bad):
    mdata = FileMetadata(paths.config)
    mdata.ledger_entry = {"uuid": "u"}
    mdata.ledger_index = 0
    args = _row_args(mdata)
    args[key] = bad
    with pytest.raises(ValueError):
        SqlFileListener(config=paths.config)._ledger_row(**args)


def test_ledger_row_values(paths):
    mdata = FileMetadata(paths.config)
    mdata.ledger_entry = {"uuid": "u", "status": "Registration failed"}
    mdata.ledger_index = 4
    row = SqlFileListener(config=paths.config)._ledger_row(**_row_args(mdata))
    assert row["uuid"] == "u"
    assert row["files_root"] == "/r"
    assert row["named_file_name"] == "orders"
    assert json.loads(row["ledger_entry"]) == mdata.ledger_entry
    assert row["ledger_index"] == 4
    assert row["status"] == "Registration failed"
    assert row["lifecycle"] is None
    assert row["version_uuid"] is None
    mdata.manifest_entry = {"uuid": "v"}
    row = SqlFileListener(config=paths.config)._ledger_row(**_row_args(mdata))
    assert row["version_uuid"] == "v"


def test_ledger_row_version_uuid_precedence(paths):
    mdata = FileMetadata(paths.config)
    mdata.ledger_entry = {"uuid": "u", "version_uuid": "m"}
    mdata.ledger_index = 0
    lst = SqlFileListener(config=paths.config)
    assert lst._ledger_row(**_row_args(mdata))["version_uuid"] == "m"
    mdata.manifest_entry = {"uuid": "v"}
    assert lst._ledger_row(**_row_args(mdata))["version_uuid"] == "v"


# ===================
# schema
# ===================


def test_new_database_has_the_ledger_tables(paths):
    engine = _engine(paths)
    Tables(paths.config, engine=engine).assure_tables()
    insp = inspect(engine)
    for table in LEDGER_TABLES:
        cols = [c["name"] for c in insp.get_columns(table)]
        assert cols == LEDGER_COLUMNS[table], table
        assert _indexes(engine, table=table) == LEDGER_INDEXES[table], table


def test_tables_define_the_ledger_indexes():
    for table, expected in LEDGER_INDEXES.items():
        got = {
            name: list(Tables.index_columns(cols))
            for name, cols in Tables.INDEXES[table].items()
        }
        assert got == expected, table


@pytest.mark.parametrize("bad", [None, "", (), ("a", ""), ("a", 3), 3, ["a"]])
def test_index_columns_rejects_bad_specs(bad):
    with pytest.raises(ValueError):
        Tables.index_columns(bad)


def test_index_columns_accepts_a_str_or_tuple():
    assert Tables.index_columns("a") == ("a",)
    assert Tables.index_columns(("a", "b")) == ("a", "b")


def _database_without_ledgers(paths: CsvPaths) -> None:
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
        ]
        Table(t.name, old, *cols)
    old.create_all(_engine(paths))


def test_first_write_to_an_existing_database_adds_the_ledger_tables(paths, tmp_path):
    _database_without_ledgers(paths)
    _register(paths, tmp_path)
    assert len(_ledger_rows(paths, table="named_file_ledger")) == 1
    for table in LEDGER_TABLES:
        assert _indexes(_engine(paths), table=table) == LEDGER_INDEXES[table]


def test_updates_create_composite_indexes_and_can_run_twice(paths):
    engine = _engine(paths)
    Tables(paths.config, engine=engine).assure_tables()
    with engine.connect() as conn:
        for name in LEDGER_INDEXES["named_file_ledger"]:
            conn.execute(text(f"DROP INDEX {name}"))
        conn.commit()
    Updates(engine).do_updates()
    Updates(engine).do_updates()
    for table in LEDGER_TABLES:
        assert _indexes(engine, table=table) == LEDGER_INDEXES[table], table


def test_check_passes_with_the_ledger_tables(paths):
    assert ReferencesSqlCheck.problems(csvpaths=paths) == []


def test_check_reports_missing_ledger_tables_and_indexes(paths, monkeypatch):
    _database_without_ledgers(paths)
    monkeypatch.setattr(Tables, "assure_tables", lambda self: None)
    monkeypatch.setattr(Updates, "do_updates", lambda self: None)
    problems = ReferencesSqlCheck.problems(csvpaths=paths)
    for table in LEDGER_TABLES:
        assert f"table {table} does not exist" in problems
    engine = _engine(paths)
    Tables(paths.config, engine=engine)._assure_table(
        Tables(paths.config, engine=engine).named_file_ledger
    )
    with engine.connect() as conn:
        conn.execute(text("DROP INDEX ix_named_file_ledger_root_name"))
        conn.commit()
    problems = ReferencesSqlCheck.problems(csvpaths=paths)
    assert "table named_file_ledger has no index ix_named_file_ledger_root_name" in (
        problems
    )
    assert "table named_file_ledger has no manifest_entry column" not in problems


# ===================
# the upsert utility
# ===================


def _table() -> Table:
    return Tables(None).named_file_ledger


@pytest.mark.parametrize("dialect", [None, "", "  ", 3])
def test_upsert_rejects_bad_dialects(dialect):
    with pytest.raises(ValueError):
        squt.upsert(dialect=dialect, table=_table(), data={"uuid": "u"}, set_={"a": 1})


def test_upsert_rejects_bad_arguments():
    with pytest.raises(ValueError):
        squt.upsert(dialect="sqlite", table=None, data={"uuid": "u"}, set_={"a": 1})
    for data in [None, {}, ["uuid"]]:
        with pytest.raises(ValueError):
            squt.upsert(dialect="sqlite", table=_table(), data=data, set_={"a": 1})
    for set_ in [None, {}, ["a"]]:
        with pytest.raises(ValueError):
            squt.upsert(dialect="sqlite", table=_table(), data={"uuid": "u"}, set_=set_)


def test_upsert_rejects_unsupported_dialects():
    with pytest.raises(NotImplementedError):
        squt.upsert(dialect="mssql", table=_table(), data={"uuid": "u"}, set_={"a": 1})
    with pytest.raises(ValueError):
        squt.upsert(dialect="oracle", table=_table(), data={"uuid": "u"}, set_={"a": 1})


@pytest.mark.parametrize("dialect", ["sqlite", "postgresql", "mysql"])
def test_upsert_builds_a_statement_for_each_supported_dialect(dialect):
    stmt = squt.upsert(
        dialect=dialect,
        table=_table(),
        data={"uuid": "u", "ledger_index": 0},
        set_={"ledger_index": 0},
    )
    assert stmt is not None


def test_upsert_of_an_existing_uuid_updates_it(paths, tmp_path):
    _register(paths, tmp_path)
    row = _ledger_rows(paths, table="named_file_ledger")[0]
    lst = SqlFileListener(config=paths.config)
    lst.csvpaths = paths
    changed = dict(row)
    #
    # read back through text() the sqlite datetime is a str
    #
    changed["at"] = datetime.fromisoformat(row["at"])
    changed["ledger_index"] = 9
    lst._upsert_ledger_row(table=lst.named_file_ledger, row=changed)
    rows = _ledger_rows(paths, table="named_file_ledger")
    assert len(rows) == 1
    assert rows[0]["ledger_index"] == 9
