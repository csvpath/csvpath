"""Deletes are events, and every ledger entry has a lifecycle (harmonization
PR 6).

FileManager.remove_named_file and PathsManager.remove_named_paths go
through Registrar.distribute_delete:

  - the registrar sets mdata.manifest_entries to the name's versions and
    mdata.change to {"time", "change": "delete"}, then removes the name's
    folder. its failure raises and stops the other listeners.
  - FilesListener / PathsListener mark every root ledger entry for the name
    "lifecycle": "deleted", in place, and append the change to each entry's
    changes list. entries already deleted are left alone. the ledger keeps
    every entry: it is the history.
  - SqlFileListener / SqlPathsListener mark the version rows deleted and
    update each ledger row to its entry as marked. updates, not upserts:
    missing rows are not backfilled.

Every new ledger entry and version row is "active"; no lifecycle is implied
by absence. Every test uses its own roots and SQLite file under pytest's
tmp_path.
"""

import copy
import json

import pytest
from sqlalchemy import create_engine, inspect, text

from csvpath import CsvPaths
from csvpath.managers.files.file_metadata import FileMetadata
from csvpath.managers.files.files_listener import FilesListener
from csvpath.managers.integrations.sql.sql_file_listener import SqlFileListener
from csvpath.managers.integrations.sql.sql_listener import SqlListener
from csvpath.managers.integrations.sql.sql_paths_listener import SqlPathsListener
from csvpath.managers.integrations.sql.updates import Updates
from csvpath.managers.listener import Listener
from csvpath.managers.paths.paths_metadata import PathsMetadata
from csvpath.managers.registrar import Registrar
from csvpath.util.box import Box
from csvpath.util.exceptions import InputException, RequiredListenerException
from csvpath.util.ledger_utility import LedgerUtility as leut

ACTIVE = "active"
DELETED = "deleted"
NO_RAISE_POLICY = "collect, print"


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
        value=f"sqlite:///{tmp_path / 'delete_ledger.db'}",
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


def _register(paths: CsvPaths, tmp_path, *, name: str = "orders", n: int = 0):
    data = tmp_path / f"{name}_{n}.csv"
    data.write_text(f"id,amount\n{n},10\n", encoding="utf-8")
    paths.file_manager.add_named_file(name=name, path=str(data))


def _fail(paths: CsvPaths) -> None:
    with pytest.raises(ValueError):
        paths.file_manager.add_named_file(name="orders", path="")


def _load(paths: CsvPaths, tmp_path, *, statement: str = "$[*][yes()]") -> None:
    f = tmp_path / "orders.csvpaths"
    f.write_text(statement, encoding="utf-8")
    paths.paths_manager.add_named_paths_from_file(name="orders", file_path=str(f))


def _manifest(paths: CsvPaths) -> list:
    #
    # a copy: the manifest can come back as a cached object
    #
    return copy.deepcopy(paths.file_manager.get_manifest("orders"))


def _ledger(paths: CsvPaths) -> list:
    return paths.file_manager.files_root_manifest or []


def _paths_ledger(paths: CsvPaths) -> list:
    return paths.paths_manager.paths_root_manifest or []


def _write_ledger(paths: CsvPaths, ledger: list) -> None:
    mpath = FilesListener(csvpaths=paths).manifest_path()
    with open(mpath, "w", encoding="utf-8") as file:
        json.dump(ledger, file, indent=2)


def _rows(paths: CsvPaths, *, sql: str) -> list[dict]:
    listener = SqlFileListener(config=paths.config)
    listener.csvpaths = paths
    with listener.engine.connect() as conn:
        return [dict(r._mapping) for r in conn.execute(text(sql))]


def _delete_file(paths: CsvPaths) -> bool:
    return paths.file_manager.remove_named_file("orders")


def _delete_paths(paths: CsvPaths) -> None:
    paths.paths_manager.remove_named_paths("orders")


class _SeesDelete(Listener):
    """records what a later listener sees when the delete reaches it"""

    def __init__(self, config, *, see) -> None:
        super().__init__(config)
        self.see = see
        self.seen = []

    def metadata_update(self, mdata) -> None:
        pass

    def metadata_delete(self, mdata) -> None:
        self.seen.append(self.see(mdata))


class _FailsDelete(Listener):
    def metadata_update(self, mdata) -> None:
        pass

    def metadata_delete(self, mdata) -> None:
        raise RuntimeError("downstream listener failed")


# ===================
# constants and defaults
# ===================


def test_lifecycle_constants():
    assert Registrar.ACTIVE == ACTIVE
    assert Registrar.DELETED == DELETED


def test_listeners_ignore_deletes_by_default(plain):
    lst = _SeesDelete(plain.config, see=lambda m: m)
    assert Listener.metadata_delete(lst, FileMetadata(plain.config)) is None


def test_metadata_has_no_delete_fields_by_default(plain):
    for m in [FileMetadata(plain.config), PathsMetadata(plain.config)]:
        assert m.manifest_entries is None
        assert m.ledger_entries is None
        assert m.change is None


# ===================
# LedgerUtility.mark_deleted
# ===================


def _mark(jdata: list, *, name: str = "orders") -> list:
    return leut.mark_deleted(
        jdata=jdata,
        name_key="named_file_name",
        name=name,
        change={"time": "t", "change": "delete"},
        deleted=DELETED,
    )


def test_mark_deleted_marks_only_the_name():
    jdata = [
        {"uuid": "a", "named_file_name": "orders", "lifecycle": ACTIVE},
        {"uuid": "b", "named_file_name": "other", "lifecycle": ACTIVE},
        {"uuid": "c", "named_file_name": "orders", "lifecycle": ACTIVE},
    ]
    marked = _mark(jdata)
    assert [e["uuid"] for e in marked] == ["a", "c"]
    assert [e["lifecycle"] for e in jdata] == [DELETED, ACTIVE, DELETED]
    assert jdata[0]["changes"] == [{"time": "t", "change": "delete"}]
    assert "changes" not in jdata[1]


def test_mark_deleted_returns_the_entries_in_place():
    jdata = [{"uuid": "a", "named_file_name": "orders", "lifecycle": ACTIVE}]
    assert _mark(jdata)[0] is jdata[0]


def test_mark_deleted_leaves_deleted_entries_alone():
    jdata = [
        {
            "uuid": "a",
            "named_file_name": "orders",
            "lifecycle": DELETED,
            "changes": [{"time": "t0", "change": "delete"}],
        }
    ]
    assert _mark(jdata) == []
    assert jdata[0]["changes"] == [{"time": "t0", "change": "delete"}]


def test_mark_deleted_marks_entries_with_no_lifecycle():
    jdata = [{"uuid": "a", "named_file_name": "orders"}]
    assert len(_mark(jdata)) == 1
    assert jdata[0]["lifecycle"] == DELETED


def test_mark_deleted_appends_to_existing_changes():
    jdata = [
        {
            "uuid": "a",
            "named_file_name": "orders",
            "lifecycle": ACTIVE,
            "changes": [{"time": "t0", "change": "patch", "from": {}}],
        }
    ]
    _mark(jdata)
    assert [c["change"] for c in jdata[0]["changes"]] == ["patch", "delete"]


def test_mark_deleted_gives_each_entry_its_own_change():
    jdata = [
        {"uuid": "a", "named_file_name": "orders", "lifecycle": ACTIVE},
        {"uuid": "b", "named_file_name": "orders", "lifecycle": ACTIVE},
    ]
    _mark(jdata)
    jdata[0]["changes"][0]["time"] = "changed"
    assert jdata[1]["changes"][0]["time"] == "t"


@pytest.mark.parametrize(
    "kwargs,error",
    [
        ({"jdata": None}, TypeError),
        ({"jdata": {}}, TypeError),
        ({"name_key": None}, ValueError),
        ({"name_key": " "}, ValueError),
        ({"name": None}, ValueError),
        ({"name": ""}, ValueError),
        ({"name": 1}, ValueError),
        ({"deleted": None}, ValueError),
        ({"change": None}, ValueError),
        ({"change": {}}, ValueError),
    ],
)
def test_mark_deleted_checks_its_arguments(kwargs, error):
    args = {
        "jdata": [],
        "name_key": "named_file_name",
        "name": "orders",
        "change": {"change": "delete"},
        "deleted": DELETED,
    }
    args.update(kwargs)
    with pytest.raises(error):
        leut.mark_deleted(**args)


# ===================
# every new ledger entry is active
# ===================


def test_a_files_arrival_is_active(plain, tmp_path):
    _register(plain, tmp_path)
    assert _ledger(plain)[0]["lifecycle"] == ACTIVE


def test_a_files_failure_is_active(plain):
    _fail(plain)
    assert _ledger(plain)[0]["status"] == "failed"
    assert _ledger(plain)[0]["lifecycle"] == ACTIVE


def test_a_paths_version_and_unchanged_reload_are_active(plain, tmp_path):
    _load(plain, tmp_path)
    _load(plain, tmp_path)
    ledger = _paths_ledger(plain)
    assert [e["status"] for e in ledger] == ["complete", "unchanged"]
    assert [e["lifecycle"] for e in ledger] == [ACTIVE, ACTIVE]


def test_per_name_entries_have_no_lifecycle(plain, tmp_path):
    #
    # status and lifecycle are ledger-only
    #
    _register(plain, tmp_path)
    _load(plain, tmp_path)
    assert "lifecycle" not in _manifest(plain)[0]
    assert "lifecycle" not in plain.paths_manager.get_manifest_for_name("orders")[0]


# ===================
# the registrars
# ===================


@pytest.mark.parametrize(
    "name,error", [(None, ValueError), (1, TypeError), ("", ValueError)]
)
def test_delete_named_file_checks_the_name(plain, name, error):
    with pytest.raises(error):
        plain.file_manager.registrar.delete_named_file(name=name)


@pytest.mark.parametrize(
    "name,error", [(None, ValueError), (1, TypeError), (" ", ValueError)]
)
def test_delete_named_paths_checks_the_name(plain, name, error):
    with pytest.raises(error):
        plain.paths_manager.registrar.delete_named_paths(name=name)


def test_registrars_check_their_metadata(plain):
    with pytest.raises(ValueError):
        plain.file_manager.registrar.metadata_delete(None)
    with pytest.raises(ValueError):
        plain.paths_manager.registrar.metadata_delete(None)


def test_deleting_an_unknown_named_file_raises(plain):
    with pytest.raises(InputException):
        plain.file_manager.registrar.delete_named_file(name="nope")


def test_deleting_an_unknown_named_paths_raises_and_creates_nothing(plain):
    with pytest.raises(InputException):
        plain.paths_manager.registrar.delete_named_paths(name="nope")
    assert not plain.paths_manager.has_named_paths("nope")


def test_the_file_registrar_records_the_deleted_versions(plain, tmp_path):
    _register(plain, tmp_path, n=0)
    _register(plain, tmp_path, n=1)
    before = _manifest(plain)
    probe = _SeesDelete(
        plain.config, see=lambda m: (copy.deepcopy(m.manifest_entries), m.change)
    )
    plain.file_manager.registrar.add_internal_listener(probe)
    assert _delete_file(plain) is True
    entries, change = probe.seen[0]
    assert entries == before
    assert change["change"] == "delete"
    assert set(change) == {"time", "change"}
    assert not plain.file_manager.has_named_file("orders")


def test_the_paths_registrar_records_the_deleted_versions(plain, tmp_path):
    _load(plain, tmp_path, statement="$[*][yes()]")
    _load(plain, tmp_path, statement="$[*][no()]")
    before = copy.deepcopy(plain.paths_manager.get_manifest_for_name("orders"))
    probe = _SeesDelete(plain.config, see=lambda m: copy.deepcopy(m.manifest_entries))
    plain.paths_manager.registrar.add_internal_listener(probe)
    _delete_paths(plain)
    assert probe.seen == [before]
    assert not plain.paths_manager.has_named_paths("orders")


def test_the_deleted_manifest_leaves_the_cache(plain, tmp_path):
    _register(plain, tmp_path)
    registrar = plain.file_manager.registrar
    home = plain.file_manager.named_file_home("orders")
    mp = registrar.manifest_path(home)
    registrar.get_manifest(mp)
    _delete_file(plain)
    assert mp not in getattr(registrar.intermediary, "_cache", {})


def test_removing_a_missing_named_file_is_not_an_event(plain, tmp_path):
    _register(plain, tmp_path)
    before = _ledger(plain)
    assert plain.file_manager.remove_named_file("other") is False
    assert _ledger(plain) == before


def test_removing_a_missing_named_paths_is_not_an_event(plain, tmp_path):
    _load(plain, tmp_path)
    before = _paths_ledger(plain)
    plain.paths_manager.remove_named_paths("other")
    assert _paths_ledger(plain) == before
    with pytest.raises(InputException):
        plain.paths_manager.remove_named_paths("other", strict=True)


def test_remove_all_named_files_deletes_each_name(plain, tmp_path):
    _register(plain, tmp_path, name="orders")
    _register(plain, tmp_path, name="other")
    plain.file_manager.remove_all_named_files()
    assert [e["lifecycle"] for e in _ledger(plain)] == [DELETED, DELETED]


# ===================
# the ledgers
# ===================


def test_a_delete_marks_the_files_ledger_in_place(plain, tmp_path):
    _register(plain, tmp_path, n=0)
    _register(plain, tmp_path, n=1)
    _delete_file(plain)
    ledger = _ledger(plain)
    assert len(ledger) == 2
    assert [e["lifecycle"] for e in ledger] == [DELETED, DELETED]
    for e in ledger:
        assert [c["change"] for c in e["changes"]] == ["delete"]
    assert ledger[0]["changes"] == ledger[1]["changes"]


def test_a_delete_marks_the_names_failures(plain, tmp_path):
    _register(plain, tmp_path)
    _fail(plain)
    _delete_file(plain)
    assert [(e["status"], e["lifecycle"]) for e in _ledger(plain)] == [
        ("complete", DELETED),
        ("failed", DELETED),
    ]


def test_a_delete_leaves_other_names_alone(plain, tmp_path):
    _register(plain, tmp_path, name="orders")
    _register(plain, tmp_path, name="other")
    _delete_file(plain)
    ledger = _ledger(plain)
    assert [e["lifecycle"] for e in ledger] == [DELETED, ACTIVE]
    assert "changes" not in ledger[1]


def test_delete_register_delete(plain, tmp_path):
    _register(plain, tmp_path, n=0)
    _delete_file(plain)
    _register(plain, tmp_path, n=1)
    assert [e["lifecycle"] for e in _ledger(plain)] == [DELETED, ACTIVE]
    assert [e["uuid"] for e in _manifest(plain)] == [_ledger(plain)[1]["uuid"]]
    _delete_file(plain)
    ledger = _ledger(plain)
    assert [e["lifecycle"] for e in ledger] == [DELETED, DELETED]
    assert [len(e["changes"]) for e in ledger] == [1, 1]
    assert ledger[0]["changes"][0]["time"] != ledger[1]["changes"][0]["time"]


def test_an_older_entry_with_no_lifecycle_is_marked(plain, tmp_path):
    _register(plain, tmp_path)
    ledger = _ledger(plain)
    del ledger[0]["lifecycle"]
    _write_ledger(plain, ledger)
    _delete_file(plain)
    assert _ledger(plain)[0]["lifecycle"] == DELETED


def test_a_patch_then_a_delete_keeps_both_changes(plain, tmp_path):
    _register(plain, tmp_path)
    plain.file_manager.registrar.patch_named_file(name="orders", patch={"type": "tsv"})
    _delete_file(plain)
    assert [c["change"] for c in _ledger(plain)[0]["changes"]] == ["patch", "delete"]


def test_the_ledger_writer_sets_ledger_entries_as_written(plain, tmp_path):
    _register(plain, tmp_path, name="orders")
    _register(plain, tmp_path, name="other")
    probe = _SeesDelete(plain.config, see=lambda m: copy.deepcopy(m.ledger_entries))
    plain.file_manager.registrar.add_internal_listener(probe)
    _delete_file(plain)
    assert probe.seen == [[_ledger(plain)[0]]]


def test_a_ledger_with_nothing_for_the_name_marks_nothing(plain, tmp_path):
    _register(plain, tmp_path)
    _write_ledger(plain, [])
    probe = _SeesDelete(plain.config, see=lambda m: m.ledger_entries)
    plain.file_manager.registrar.add_internal_listener(probe)
    _delete_file(plain)
    assert probe.seen == [[]]
    assert _ledger(plain) == []


def test_ledger_writers_check_their_metadata(plain):
    for lst in [
        FilesListener(csvpaths=plain),
        plain.paths_manager.registrar._built_in_listeners[0],
    ]:
        with pytest.raises(ValueError):
            lst.metadata_delete(None)
        with pytest.raises(ValueError, match="no delete change"):
            lst.metadata_delete(FileMetadata(plain.config))


def test_a_delete_marks_the_paths_ledger_in_place(plain, tmp_path):
    _load(plain, tmp_path, statement="$[*][yes()]")
    _load(plain, tmp_path, statement="$[*][yes()]")
    _delete_paths(plain)
    _load(plain, tmp_path, statement="$[*][no()]")
    ledger = _paths_ledger(plain)
    assert [(e["status"], e["lifecycle"]) for e in ledger] == [
        ("complete", DELETED),
        ("unchanged", DELETED),
        ("complete", ACTIVE),
    ]
    assert [c["change"] for c in ledger[1]["changes"]] == ["delete"]
    assert "changes" not in ledger[2]
    per_name = plain.paths_manager.get_manifest_for_name("orders")
    assert [e["uuid"] for e in per_name] == [ledger[2]["uuid"]]


# ===================
# distribution
# ===================


def test_later_listeners_see_the_folder_gone_and_the_ledger_marked(plain, tmp_path):
    _register(plain, tmp_path)
    probe = _SeesDelete(
        plain.config,
        see=lambda m: (
            plain.file_manager.has_named_file("orders"),
            _ledger(plain)[0]["lifecycle"],
        ),
    )
    plain.file_manager.registrar.add_internal_listener(probe)
    _delete_file(plain)
    assert probe.seen == [(False, DELETED)]


def test_a_registrar_failure_stops_the_delete(plain, tmp_path):
    _register(plain, tmp_path)
    probe = _SeesDelete(plain.config, see=lambda m: True)
    plain.file_manager.registrar.add_internal_listener(probe)
    with pytest.raises(InputException):
        plain.file_manager.registrar.delete_named_file(name="nope")
    assert probe.seen == []
    assert _ledger(plain)[0]["lifecycle"] == ACTIVE


def test_a_downstream_failure_is_logged_not_raised(plain, tmp_path):
    plain.config.add_to_config(section="errors", key="csvpaths", value=NO_RAISE_POLICY)
    _register(plain, tmp_path)
    plain.file_manager.registrar.add_internal_listener(_FailsDelete(plain.config))
    assert _delete_file(plain) is True
    assert not plain.file_manager.has_named_file("orders")
    assert _ledger(plain)[0]["lifecycle"] == DELETED


# ===================
# SQL
# ===================


def test_new_version_rows_are_active(sql, tmp_path):
    _register(sql, tmp_path)
    _load(sql, tmp_path)
    assert _rows(sql, sql="select lifecycle from named_file") == [
        {"lifecycle": ACTIVE}
    ]
    assert _rows(sql, sql="select lifecycle from named_paths") == [
        {"lifecycle": ACTIVE}
    ]


def test_sql_marks_the_deleted_named_file_versions(sql, tmp_path):
    _register(sql, tmp_path, n=0)
    a = _manifest(sql)[0]["uuid"]
    _delete_file(sql)
    _register(sql, tmp_path, n=1)
    b = _manifest(sql)[0]["uuid"]
    rows = _rows(sql, sql="select uuid, lifecycle from named_file")
    assert {r["uuid"]: r["lifecycle"] for r in rows} == {a: DELETED, b: ACTIVE}


def test_sql_ledger_rows_mirror_the_marked_entries(sql, tmp_path):
    _register(sql, tmp_path, n=0)
    _fail(sql)
    before = _rows(
        sql, sql="select uuid, at, ledger_index from named_file_ledger order by uuid"
    )
    _delete_file(sql)
    rows = _rows(sql, sql="select * from named_file_ledger order by ledger_index")
    assert [json.loads(r["ledger_entry"]) for r in rows] == _ledger(sql)
    assert [r["lifecycle"] for r in rows] == [DELETED, DELETED]
    assert [r["status"] for r in rows] == ["complete", "failed"]
    after = _rows(
        sql, sql="select uuid, at, ledger_index from named_file_ledger order by uuid"
    )
    assert after == before


def test_sql_marks_the_deleted_named_paths(sql, tmp_path):
    _load(sql, tmp_path, statement="$[*][yes()]")
    _load(sql, tmp_path, statement="$[*][yes()]")
    _delete_paths(sql)
    _load(sql, tmp_path, statement="$[*][no()]")
    versions = _rows(sql, sql="select lifecycle from named_paths order by at")
    assert [r["lifecycle"] for r in versions] == [DELETED, ACTIVE]
    rows = _rows(sql, sql="select * from named_paths_ledger order by ledger_index")
    assert [json.loads(r["ledger_entry"]) for r in rows] == _paths_ledger(sql)
    assert [r["lifecycle"] for r in rows] == [DELETED, DELETED, ACTIVE]


def test_sql_does_not_backfill_missing_rows(sql, tmp_path):
    _register(sql, tmp_path)
    listener = SqlFileListener(config=sql.config)
    listener.csvpaths = sql
    with listener.engine.connect() as conn:
        conn.execute(text("delete from named_file"))
        conn.execute(text("delete from named_file_ledger"))
        conn.commit()
    assert _delete_file(sql) is True
    assert _rows(sql, sql="select uuid from named_file") == []
    assert _rows(sql, sql="select uuid from named_file_ledger") == []
    assert _ledger(sql)[0]["lifecycle"] == DELETED


def test_a_failed_sql_delete_raises_required_under_on(sql, tmp_path, monkeypatch):
    sql.config.add_to_config(section="errors", key="csvpaths", value=NO_RAISE_POLICY)
    _register(sql, tmp_path)
    sql.config.add_to_config(section="references", key="sql", value="on")

    def fail(self, **kwargs):
        raise RuntimeError("delete rows failed")

    monkeypatch.setattr(SqlListener, "_mark_deleted", fail)
    with pytest.raises(RequiredListenerException, match="SqlFileListener"):
        _delete_file(sql)
    assert _ledger(sql)[0]["lifecycle"] == DELETED


@pytest.mark.parametrize("cls", [SqlFileListener, SqlPathsListener])
def test_mark_deleted_checks_its_arguments(sql, cls):
    listener = cls(config=sql.config)
    listener.csvpaths = sql
    table = listener.tables.named_file
    with pytest.raises(ValueError):
        listener._mark_deleted(
            mdata=None, version_table=table, ledger_table=table, name="orders"
        )
    with pytest.raises(ValueError):
        listener._mark_deleted(
            mdata=FileMetadata(sql.config),
            version_table=None,
            ledger_table=table,
            name="orders",
        )


@pytest.mark.parametrize("cls", [SqlFileListener, SqlPathsListener])
def test_sql_listeners_require_csvpaths_for_deletes(sql, cls):
    with pytest.raises(RuntimeError):
        cls(config=sql.config).metadata_delete(FileMetadata(sql.config))


def test_updates_add_lifecycle_to_older_version_tables(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'old.db'}")
    with engine.connect() as conn:
        conn.execute(text("create table named_file (uuid varchar(40))"))
        conn.execute(text("create table named_paths (uuid varchar(40))"))
        conn.commit()
    Updates(engine).do_updates()
    for table in ["named_file", "named_paths"]:
        columns = [c["name"] for c in inspect(engine).get_columns(table)]
        assert "lifecycle" in columns
    engine.dispose()
