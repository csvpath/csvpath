"""Removing a named-results group is an event (step 4c-3), as removing a
named-file or named-paths group is (#458).

ResultsManager.remove_named_results goes through RunRegistrar, the
archive ledger's registrar and writer, and Registrar.distribute_delete:

  - RunRegistrar removes the group's results folder, then marks every
    archive ledger entry for the group "lifecycle": "deleted", in place,
    with a {"time", "change": "delete"} change, and sets
    mdata.ledger_entries. entries already deleted are left alone. the
    ledger keeps every entry.
  - SqlRunListener updates each archive_ledger row to its entry as marked,
    and marks the entries' instance_run and named_paths_group_run rows
    deleted. updates, not upserts.

New group run and instance rows are "active". Under [references] sql =
on, run and instance reads skip rows that are not active.

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
from csvpath.managers.integrations.sql.updates import Updates
from csvpath.managers.listener import Listener
from csvpath.managers.run.run_metadata import RunMetadata
from csvpath.managers.run.run_registrar import RunRegistrar
from csvpath.references.sources.filesystem_reference_source import (
    FilesystemReferenceSource,
)
from csvpath.references.sources.sql_reference_source import SqlReferenceSource
from csvpath.util.box import Box
from csvpath.util.exceptions import InputException, RequiredListenerException
from csvpath.util.nos import Nos

GROUP = """~ id: first ~ $[*][yes()]

---- CSVPATH ----

~ id: second ~ $[*][yes()]"""


def _clear_engine() -> None:
    box = Box()
    e = box.get(key=Box.SQL_ENGINE)
    if e is not None:
        e.dispose()
        box.remove(Box.SQL_ENGINE)


def _paths(tmp_path, *, groups: str) -> CsvPaths:
    p = CsvPaths()
    c = p.config
    c.add_to_config(section="inputs", key="files", value=str(tmp_path / "nf"))
    c.add_to_config(section="inputs", key="csvpaths", value=str(tmp_path / "np"))
    c.add_to_config(section="results", key="archive", value=str(tmp_path / "ar"))
    c.add_to_config(section="listeners", key="groups", value=groups)
    c.add_to_config(section="sql", key="dialect", value="sqlite")
    c.add_to_config(
        section="sql",
        key="connection_string",
        value=f"sqlite:///{tmp_path / 'results_delete.db'}",
    )
    return p


@pytest.fixture
def plain(tmp_path):
    _clear_engine()
    yield _paths(tmp_path, groups="")
    _clear_engine()


@pytest.fixture
def sql(tmp_path):
    _clear_engine()
    yield _paths(tmp_path, groups="sql")
    _clear_engine()


def _run(p: CsvPaths, tmp_path, *, name: str = "orders") -> None:
    data = tmp_path / "orders.csv"
    data.write_text("id,amount\n1,10\n", encoding="utf-8")
    if not p.file_manager.has_named_file("orders"):
        p.file_manager.add_named_file(name="orders", path=str(data))
    group = tmp_path / f"{name}.csvpaths"
    group.write_text(GROUP, encoding="utf-8")
    if not p.paths_manager.has_named_paths(name):
        p.paths_manager.add_named_paths_from_file(name=name, file_path=str(group))
    p.collect_paths(pathsname=name, filename="orders")


def _ledger(p: CsvPaths) -> list:
    return p.results_manager.results_root_manifest


def _home(p: CsvPaths, name: str = "orders") -> str:
    return p.results_manager.get_named_results_home(name)


def _rows(p: CsvPaths, *, sql: str) -> list[dict]:
    listener = SqlRunListener(config=p.config)
    listener.csvpaths = p
    with listener.engine.connect() as conn:
        return [dict(r._mapping) for r in conn.execute(text(sql))]


class _SeesDelete(Listener):
    def __init__(self, config, *, see) -> None:
        super().__init__(config)
        self.see = see
        self.seen = []

    def metadata_update(self, mdata) -> None:
        pass

    def metadata_delete(self, mdata) -> None:
        self.seen.append(self.see(mdata))


def _delete_with(p: CsvPaths, *, probe, name: str = "orders") -> None:
    rr = RunRegistrar(csvpaths=p)
    rr.add_internal_listener(probe)
    rr.delete_named_results(name=name)


# ===================
# active rows
# ===================


def test_new_group_run_and_instance_rows_are_active(sql, tmp_path):
    _run(sql, tmp_path)
    assert _rows(sql, sql="select lifecycle from named_paths_group_run") == [
        {"lifecycle": "active"}
    ]
    assert _rows(sql, sql="select lifecycle from instance_run") == [
        {"lifecycle": "active"},
        {"lifecycle": "active"},
    ]


# ===================
# the registrar
# ===================


@pytest.mark.parametrize("name,error", [(None, ValueError), (1, TypeError), ("", ValueError)])
def test_delete_named_results_checks_the_name(plain, name, error):
    with pytest.raises(error):
        RunRegistrar(csvpaths=plain).delete_named_results(name=name)


def test_metadata_delete_checks_its_metadata(plain):
    with pytest.raises(ValueError):
        RunRegistrar(csvpaths=plain).metadata_delete(None)


def test_an_unknown_name_raises(plain):
    with pytest.raises(InputException):
        RunRegistrar(csvpaths=plain).delete_named_results(name="nope")


def test_a_missing_results_home_is_not_an_event(plain, tmp_path):
    _run(plain, tmp_path)
    before = _ledger(plain)
    plain.results_manager.remove_named_results("other")
    assert _ledger(plain) == before


def test_the_folder_is_removed_and_the_ledger_marked(plain, tmp_path):
    _run(plain, tmp_path)
    _run(plain, tmp_path)
    plain.results_manager.remove_named_results("orders")
    assert not Nos(_home(plain)).dir_exists()
    ledger = _ledger(plain)
    assert len(ledger) == 4
    assert [e["lifecycle"] for e in ledger] == ["deleted"] * 4
    assert [e["status"] for e in ledger] == ["started"] * 4
    for e in ledger:
        assert [c["change"] for c in e["changes"]] == ["delete"]
    assert len({json.dumps(e["changes"]) for e in ledger}) == 1


def test_other_groups_are_left_alone(plain, tmp_path):
    _run(plain, tmp_path, name="orders")
    _run(plain, tmp_path, name="beta")
    plain.results_manager.remove_named_results("orders")
    by_group = {(e["named_paths_name"], e["lifecycle"]) for e in _ledger(plain)}
    assert by_group == {("orders", "deleted"), ("beta", "active")}
    assert Nos(_home(plain, "beta")).dir_exists()


def test_a_reference_name_is_resolved(plain, tmp_path):
    _run(plain, tmp_path)
    plain.results_manager.remove_named_results("$orders.results.2026-01-01_:first")
    assert not Nos(_home(plain)).dir_exists()
    assert {e["lifecycle"] for e in _ledger(plain)} == {"deleted"}


def test_delete_run_delete(plain, tmp_path):
    _run(plain, tmp_path)
    plain.results_manager.remove_named_results("orders")
    _run(plain, tmp_path)
    assert [e["lifecycle"] for e in _ledger(plain)] == [
        "deleted",
        "deleted",
        "active",
        "active",
    ]
    plain.results_manager.remove_named_results("orders")
    ledger = _ledger(plain)
    assert [e["lifecycle"] for e in ledger] == ["deleted"] * 4
    assert [len(e["changes"]) for e in ledger] == [1, 1, 1, 1]


def test_ledger_entries_are_the_marked_entries(plain, tmp_path):
    _run(plain, tmp_path, name="orders")
    _run(plain, tmp_path, name="beta")
    probe = _SeesDelete(plain.config, see=lambda m: m.ledger_entries)
    _delete_with(plain, probe=probe)
    marked = [e for e in _ledger(plain) if e["named_paths_name"] == "orders"]
    assert probe.seen == [marked]


def test_later_listeners_see_the_folder_gone(plain, tmp_path):
    _run(plain, tmp_path)
    probe = _SeesDelete(plain.config, see=lambda m: Nos(_home(plain)).dir_exists())
    _delete_with(plain, probe=probe)
    assert probe.seen == [False]


def test_a_registrar_failure_stops_the_delete(plain, tmp_path):
    _run(plain, tmp_path)
    probe = _SeesDelete(plain.config, see=lambda m: True)
    with pytest.raises(InputException):
        _delete_with(plain, probe=probe, name="nope")
    assert probe.seen == []
    assert {e["lifecycle"] for e in _ledger(plain)} == {"active"}


# ===================
# SQL
# ===================


def test_sql_marks_the_ledger_rows_runs_and_instances(sql, tmp_path):
    _run(sql, tmp_path, name="orders")
    _run(sql, tmp_path, name="beta")
    before = _rows(
        sql, sql="select uuid, at, ledger_index from archive_ledger order by uuid"
    )
    sql.results_manager.remove_named_results("orders")
    rows = _rows(sql, sql="select * from archive_ledger order by ledger_index")
    assert [json.loads(r["ledger_entry"]) for r in rows] == _ledger(sql)
    assert [(r["named_paths_name"], r["lifecycle"]) for r in rows] == [
        ("orders", "deleted"),
        ("orders", "deleted"),
        ("beta", "active"),
        ("beta", "active"),
    ]
    after = _rows(
        sql, sql="select uuid, at, ledger_index from archive_ledger order by uuid"
    )
    assert after == before
    runs = _rows(sql, sql="select named_paths_name, lifecycle from named_paths_group_run")
    assert sorted((r["named_paths_name"], r["lifecycle"]) for r in runs) == [
        ("beta", "active"),
        ("orders", "deleted"),
    ]
    instances = _rows(
        sql,
        sql="select g.named_paths_name, i.lifecycle from instance_run i "
        "join named_paths_group_run g on g.uuid = i.group_run_uuid",
    )
    assert sorted((r["named_paths_name"], r["lifecycle"]) for r in instances) == [
        ("beta", "active"),
        ("beta", "active"),
        ("orders", "deleted"),
        ("orders", "deleted"),
    ]


def test_sql_does_not_backfill_missing_rows(sql, tmp_path):
    _run(sql, tmp_path)
    listener = SqlRunListener(config=sql.config)
    listener.csvpaths = sql
    with listener.engine.connect() as conn:
        for t in ["archive_ledger", "instance_run", "named_paths_group_run"]:
            conn.execute(text(f"delete from {t}"))
        conn.commit()
    sql.results_manager.remove_named_results("orders")
    for t in ["archive_ledger", "instance_run", "named_paths_group_run"]:
        assert _rows(sql, sql=f"select uuid from {t}") == []
    assert {e["lifecycle"] for e in _ledger(sql)} == {"deleted"}


def test_a_failed_sql_delete_raises_required_under_on(sql, tmp_path, monkeypatch):
    sql.config.add_to_config(section="errors", key="csvpaths", value="collect, print")
    _run(sql, tmp_path)
    sql.config.add_to_config(section="references", key="sql", value="on")

    def fail(self, **kwargs):
        raise RuntimeError("delete rows failed")

    monkeypatch.setattr(SqlListener, "_update_by_uuid_unreliably", fail)
    with pytest.raises(RequiredListenerException, match="SqlRunListener"):
        sql.results_manager.remove_named_results("orders")
    assert {e["lifecycle"] for e in _ledger(sql)} == {"deleted"}


def test_the_sql_listener_checks_its_input(sql):
    listener = SqlRunListener(config=sql.config)
    with pytest.raises(RuntimeError):
        listener.metadata_delete(RunMetadata(sql.config))
    listener.csvpaths = sql
    with pytest.raises(ValueError):
        listener.metadata_delete(None)


# ===================
# reads under on
# ===================


def test_deleted_runs_and_instances_are_not_read(sql, tmp_path):
    _run(sql, tmp_path)
    s = SqlReferenceSource(csvpaths=sql)
    home = s.run_homes(root_major="orders", name_filter=None)[0][0]
    dirs = sorted(s.instance_dirs(home))
    assert s.run_manifest(home) is not None
    #
    # mark the rows only, keeping every file, so the filter is what hides
    # them
    #
    with s.engine.connect() as conn:
        conn.execute(text("update named_paths_group_run set lifecycle = 'deleted'"))
        conn.execute(text("update instance_run set lifecycle = 'deleted'"))
        conn.commit()
    assert s.run_manifest(home) is None
    assert s.instance_dirs(home) == []
    assert s.instance_manifest(Nos(home).join(dirs[0])) is None


def test_rows_with_no_lifecycle_are_not_read(sql, tmp_path):
    _run(sql, tmp_path)
    s = SqlReferenceSource(csvpaths=sql)
    home = s.run_homes(root_major="orders", name_filter=None)[0][0]
    with s.engine.connect() as conn:
        conn.execute(text("update named_paths_group_run set lifecycle = NULL"))
        conn.execute(text("update instance_run set lifecycle = NULL"))
        conn.commit()
    assert s.run_manifest(home) is None
    assert s.instance_dirs(home) == []


def test_both_sources_drop_a_deleted_group(sql, tmp_path):
    _run(sql, tmp_path, name="orders")
    _run(sql, tmp_path, name="beta")
    sql.results_manager.remove_named_results("orders")
    args = {"root_major": None, "name_filter": None}
    fs = FilesystemReferenceSource(csvpaths=sql).run_homes(**args)
    on = SqlReferenceSource(csvpaths=sql).run_homes(**args)
    assert fs == on
    assert [g for _, g in on] == ["beta"]


# ===================
# schema and the check
# ===================


def test_updates_add_lifecycle_to_older_run_tables(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'old.db'}")
    try:
        with engine.connect() as conn:
            conn.execute(text("create table named_paths_group_run (uuid varchar(40))"))
            conn.execute(text("create table instance_run (uuid varchar(40))"))
            conn.commit()
        Updates(engine).do_updates()
        for table in ["named_paths_group_run", "instance_run"]:
            cols = [c["name"] for c in inspect(engine).get_columns(table)]
            assert "lifecycle" in cols, table
    finally:
        engine.dispose()


@pytest.mark.parametrize("table", ["named_paths_group_run", "instance_run"])
def test_the_check_requires_lifecycle_on_run_tables(sql, table):
    s = SqlReferenceSource(csvpaths=sql)
    s.tables.assure_tables()
    assert ReferencesSqlCheck._missing(engine=s.engine) == []
    with s.engine.connect() as conn:
        conn.execute(text(f"alter table {table} drop column lifecycle"))
        conn.commit()
    assert ReferencesSqlCheck._missing(engine=s.engine) == [
        f"table {table} has no lifecycle column"
    ]
