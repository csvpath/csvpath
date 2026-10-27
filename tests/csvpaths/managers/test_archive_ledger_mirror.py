"""The archive ledger and its SQL mirror (step 4c-1).

RunRegistrar appends one entry to the archive's manifest.json per
instance run, as it starts. Each entry now has "status": "started" (the
run's own manifest says when it completes) and "lifecycle": "active", and
RunRegistrar sets mdata.ledger_entry and mdata.ledger_index.

SqlRunListener (sql.run, for run events) mirrors each entry into
archive_ledger: the exact entry, its position, the archive root, the
group's name, status, lifecycle and run_uuid, which links to the
named_paths_group_run row. named_paths_group_run gets an archive_root
column, the way named_file has files_root.

Every test uses its own roots and SQLite file under pytest's tmp_path.
"""

import json

import pytest
from sqlalchemy import create_engine, inspect, text

from csvpath import CsvPaths
from csvpath.managers.integrations.sql.references_sql_check import (
    ReferencesSqlCheck,
)
from csvpath.managers.integrations.sql.sql_listener import SqlListener
from csvpath.managers.integrations.sql.sql_run_listener import SqlRunListener
from csvpath.managers.integrations.sql.tables import Tables
from csvpath.managers.integrations.sql.updates import Updates
from csvpath.managers.registrar import Registrar
from csvpath.managers.results.results_registrar import ResultsRegistrar
from csvpath.managers.run.run_metadata import RunMetadata
from csvpath.managers.run.run_registrar import RunRegistrar
from csvpath.util.box import Box
from csvpath.util.config import Config
from csvpath.util.exceptions import RequiredListenerException

GROUP = """~ id: first ~ $[*][yes()]

---- CSVPATH ----

~ id: second ~ $[*][yes()]"""

RUN_LISTENER = (
    "sql.run = from csvpath.managers.integrations.sql.sql_run_listener "
    "import SqlRunListener"
)


def _clear_engine() -> None:
    box = Box()
    e = box.get(key=Box.SQL_ENGINE)
    if e is not None:
        e.dispose()
        box.remove(Box.SQL_ENGINE)


def _paths(tmp_path, *, groups: str = "sql", root: str = "a") -> CsvPaths:
    p = CsvPaths()
    c = p.config
    c.add_to_config(section="inputs", key="files", value=str(tmp_path / root / "nf"))
    c.add_to_config(section="inputs", key="csvpaths", value=str(tmp_path / root / "np"))
    c.add_to_config(section="results", key="archive", value=str(tmp_path / root / "ar"))
    c.add_to_config(section="listeners", key="groups", value=groups)
    c.add_to_config(section="sql", key="dialect", value="sqlite")
    c.add_to_config(
        section="sql",
        key="connection_string",
        value=f"sqlite:///{tmp_path / 'archive_ledger.db'}",
    )
    return p


@pytest.fixture
def sql(tmp_path):
    _clear_engine()
    yield _paths(tmp_path)
    _clear_engine()


@pytest.fixture
def plain(tmp_path):
    _clear_engine()
    yield _paths(tmp_path, groups="")
    _clear_engine()


def _run(p: CsvPaths, tmp_path, *, name: str = "orders") -> None:
    data = tmp_path / f"{name}.csv"
    data.write_text("id,amount\n1,10\n2,20\n", encoding="utf-8")
    if not p.file_manager.has_named_file(name):
        p.file_manager.add_named_file(name=name, path=str(data))
    group = tmp_path / f"{name}.csvpaths"
    group.write_text(GROUP, encoding="utf-8")
    if not p.paths_manager.has_named_paths(name):
        p.paths_manager.add_named_paths_from_file(name=name, file_path=str(group))
    p.collect_paths(pathsname=name, filename=name)


def _ledger(p: CsvPaths) -> list:
    return p.results_manager.results_root_manifest


def _rows(p: CsvPaths, *, sql: str) -> list[dict]:
    listener = SqlRunListener(config=p.config)
    listener.csvpaths = p
    with listener.engine.connect() as conn:
        return [dict(r._mapping) for r in conn.execute(text(sql))]


def _archive_rows(p: CsvPaths) -> list[dict]:
    return _rows(p, sql="select * from archive_ledger order by ledger_index")


def _run_metadata(p: CsvPaths) -> RunMetadata:
    m = RunMetadata(p.config)
    m.run_home = str(p.config.archive_path) + "/orders/2026-01-01_00-00-00"
    m.named_paths_name = "orders"
    m.named_file_name = "orders"
    m.identity = "first"
    return m


# ===================
# the archive ledger entries
# ===================


def test_started_is_one_string():
    assert Registrar.STARTED == ResultsRegistrar.STARTED == "started"


def test_entries_are_started_and_active(plain, tmp_path):
    _run(plain, tmp_path)
    ledger = _ledger(plain)
    assert len(ledger) == 2
    assert [(e["status"], e["lifecycle"]) for e in ledger] == [
        ("started", "active"),
        ("started", "active"),
    ]


def test_the_registrar_sets_the_ledger_entry_and_index(plain, tmp_path):
    _run(plain, tmp_path)
    m = _run_metadata(plain)
    RunRegistrar(csvpaths=plain).metadata_update(m)
    ledger = _ledger(plain)
    assert m.ledger_entry == ledger[-1]
    assert m.ledger_index == len(ledger) - 1 == 2


def test_a_new_archive_starts_at_index_zero(plain):
    m = _run_metadata(plain)
    RunRegistrar(csvpaths=plain).metadata_update(m)
    assert m.ledger_index == 0
    assert _ledger(plain) == [m.ledger_entry]


# ===================
# the SQL mirror
# ===================


def test_rows_mirror_the_entries_exactly(sql, tmp_path):
    _run(sql, tmp_path)
    _run(sql, tmp_path)
    ledger = _ledger(sql)
    rows = _archive_rows(sql)
    assert len(ledger) == 4
    assert [json.loads(r["ledger_entry"]) for r in rows] == ledger
    assert [r["ledger_index"] for r in rows] == [0, 1, 2, 3]
    assert [r["uuid"] for r in rows] == [e["uuid"] for e in ledger]


def test_rows_have_the_root_name_status_and_lifecycle(sql, tmp_path):
    _run(sql, tmp_path)
    for r in _archive_rows(sql):
        assert r["archive_root"] == sql.config.archive_path
        assert r["named_paths_name"] == "orders"
        assert r["status"] == "started"
        assert r["lifecycle"] == "active"


def test_run_uuid_links_the_group_run(sql, tmp_path):
    _run(sql, tmp_path)
    group_runs = _rows(sql, sql="select uuid from named_paths_group_run")
    rows = _archive_rows(sql)
    assert {r["run_uuid"] for r in rows} == {g["uuid"] for g in group_runs}
    assert [r["run_uuid"] for r in rows] == [e["run_uuid"] for e in _ledger(sql)]


def test_group_runs_have_the_archive_root(sql, tmp_path):
    _run(sql, tmp_path)
    rows = _rows(sql, sql="select archive_root from named_paths_group_run")
    assert rows == [{"archive_root": sql.config.archive_path}]


def test_rows_are_scoped_by_archive_root(sql, tmp_path):
    _run(sql, tmp_path)
    other = _paths(tmp_path, root="b")
    _run(other, tmp_path / "b", name="orders")
    roots = _rows(
        sql,
        sql="select archive_root, count(*) as n from archive_ledger group by archive_root",
    )
    assert {r["archive_root"]: r["n"] for r in roots} == {
        sql.config.archive_path: 2,
        other.config.archive_path: 2,
    }


def test_no_ledger_entry_means_no_row(sql):
    listener = SqlRunListener(config=sql.config)
    listener.csvpaths = sql
    listener.tables.assure_tables()
    listener.metadata_update(_run_metadata(sql))
    assert _archive_rows(sql) == []


def test_without_the_sql_group_nothing_is_written(plain, tmp_path):
    _run(plain, tmp_path)
    engine = create_engine(plain.config.get(section="sql", name="connection_string"))
    try:
        assert not inspect(engine).has_table("archive_ledger")
    finally:
        engine.dispose()


def test_a_failed_row_raises_required_under_on(sql, monkeypatch):
    sql.config.add_to_config(section="errors", key="csvpaths", value="collect, print")
    sql.config.add_to_config(section="references", key="sql", value="on")

    def fail(self, *, table, row):
        raise RuntimeError("archive row failed")

    monkeypatch.setattr(SqlListener, "_upsert_ledger_row_unreliably", fail)
    m = _run_metadata(sql)
    with pytest.raises(RequiredListenerException, match="SqlRunListener"):
        RunRegistrar(csvpaths=sql).register_start(m)
    assert _ledger(sql) == [m.ledger_entry]


# ===================
# SqlRunListener checks
# ===================


def test_csvpaths_is_required(sql):
    with pytest.raises(RuntimeError):
        SqlRunListener(config=sql.config).metadata_update(_run_metadata(sql))


def test_metadata_is_required(sql):
    listener = SqlRunListener(config=sql.config)
    listener.csvpaths = sql
    with pytest.raises(ValueError):
        listener.metadata_update(None)


@pytest.mark.parametrize(
    "change",
    [
        {"ledger_index": None},
        {"ledger_entry": None},
        {"archive_path": ""},
        {"archive_path": None},
        {"entry_name": None},
        {"entry_name": " "},
    ],
)
def test_the_row_checks_its_metadata(sql, change):
    listener = SqlRunListener(config=sql.config)
    listener.csvpaths = sql
    m = _run_metadata(sql)
    m.ledger_entry = {"uuid": "u", "named_paths_name": "orders"}
    m.ledger_index = 0
    if "entry_name" in change:
        m.ledger_entry["named_paths_name"] = change["entry_name"]
    else:
        key, value = next(iter(change.items()))
        setattr(m, key, value)
    with pytest.raises(ValueError):
        listener._archive_ledger_row(m)


# ===================
# schema, updates and the check
# ===================


def test_the_table_and_its_indexes(sql):
    engine = SqlRunListener(config=sql.config).engine
    Tables(sql.config, engine=engine).assure_tables()
    insp = inspect(engine)
    cols = [c["name"] for c in insp.get_columns("archive_ledger")]
    assert cols == [
        "uuid",
        "at",
        "archive_root",
        "named_paths_name",
        "ledger_entry",
        "ledger_index",
        "status",
        "lifecycle",
        "run_uuid",
    ]
    indexes = {i["name"]: i["column_names"] for i in insp.get_indexes("archive_ledger")}
    assert indexes == {
        "ix_archive_ledger_root_index": ["archive_root", "ledger_index"],
        "ix_archive_ledger_root_name": ["archive_root", "named_paths_name"],
    }


def test_updates_add_archive_root_to_an_older_group_run_table(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'old.db'}")
    try:
        with engine.connect() as conn:
            conn.execute(
                text(
                    "create table named_paths_group_run (uuid varchar(40), "
                    "named_paths_name varchar(45), run_home varchar(250))"
                )
            )
            conn.commit()
        Updates(engine).do_updates()
        insp = inspect(engine)
        cols = [c["name"] for c in insp.get_columns("named_paths_group_run")]
        assert "archive_root" in cols
        names = [i["name"] for i in insp.get_indexes("named_paths_group_run")]
        assert "ix_named_paths_group_run_archive_root" in names
    finally:
        engine.dispose()


def test_the_check_requires_the_run_listener(sql):
    assert ReferencesSqlCheck.LISTENERS["run"] == "SqlRunListener"
    assert "archive_ledger" in ReferencesSqlCheck.LEDGER_TABLES


def test_the_check_reports_a_missing_archive_ledger_and_root(sql):
    engine = SqlRunListener(config=sql.config).engine
    Tables(sql.config, engine=engine).assure_tables()
    assert ReferencesSqlCheck._missing(engine=engine) == []
    with engine.connect() as conn:
        conn.execute(text("drop table archive_ledger"))
        conn.execute(text("drop index ix_named_paths_group_run_archive_root"))
        conn.execute(text("alter table named_paths_group_run drop column archive_root"))
        conn.commit()
    problems = ReferencesSqlCheck._missing(engine=engine)
    assert "table archive_ledger does not exist" in problems
    assert "table named_paths_group_run has no archive_root column" in problems


def test_the_default_config_lists_the_run_listener():
    assert RUN_LISTENER in Config.DEFAULT_CONFIG
