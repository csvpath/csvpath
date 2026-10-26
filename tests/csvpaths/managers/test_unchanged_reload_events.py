"""Unchanged named-paths reloads are marked (harmonization PR 4).
Loading a group whose fingerprint matches its most recent version writes
no version, but the root ledger still records the load. That entry now
has status "unchanged" and version_uuid, the uuid of the version it
matched. The SQL ledger row mirrors both, so version_uuid comes from the
entry, not from a lookup.

Every test uses its own roots and SQLite file under pytest's tmp_path.
"""

import json

import pytest
from sqlalchemy import text

from csvpath import CsvPaths
from csvpath.managers.integrations.sql.sql_paths_listener import SqlPathsListener
from csvpath.managers.listener import Listener
from csvpath.managers.paths.paths_metadata import PathsMetadata
from csvpath.managers.paths.paths_registrar import PathsRegistrar
from csvpath.util.box import Box

UNCHANGED = "unchanged"


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
        value=f"sqlite:///{tmp_path / 'unchanged.db'}",
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


def _load(paths: CsvPaths, tmp_path, *, statement: str = "$[*][yes()]") -> None:
    f = tmp_path / "orders.csvpaths"
    f.write_text(statement, encoding="utf-8")
    paths.paths_manager.add_named_paths_from_file(name="orders", file_path=str(f))


def _ledger(paths: CsvPaths) -> list:
    return paths.paths_manager.paths_root_manifest or []


def _manifest_path(paths: CsvPaths) -> str:
    return paths.paths_manager.registrar.manifest_path("orders")


def _versions(paths: CsvPaths) -> list:
    return paths.paths_manager.registrar.get_manifest(_manifest_path(paths))


def _rows(paths: CsvPaths, *, sql: str) -> list[dict]:
    listener = SqlPathsListener(config=paths.config)
    listener.csvpaths = paths
    with listener.engine.connect() as conn:
        return [dict(r._mapping) for r in conn.execute(text(sql))]


def _ledger_rows(paths: CsvPaths) -> list[dict]:
    return _rows(paths, sql="select * from named_paths_ledger order by ledger_index")


class _Recording(Listener):
    """records the updates it is sent"""

    def __init__(self, config=None) -> None:
        super().__init__(config)
        self.updates = []

    def metadata_update(self, mdata) -> None:
        self.updates.append(mdata)


# ===================
# the fields
# ===================


def test_paths_metadata_fields_default_to_none(plain):
    mdata = PathsMetadata(plain.config)
    assert mdata.status is None
    assert mdata.version_uuid is None


def test_the_unchanged_status(plain):
    assert PathsRegistrar.UNCHANGED == UNCHANGED


# ===================
# the ledger entry
# ===================


def test_a_first_load_is_not_marked(plain, tmp_path):
    _load(plain, tmp_path)
    entry = _ledger(plain)[0]
    assert "status" not in entry
    assert "version_uuid" not in entry


def test_an_unchanged_reload_is_marked_and_names_its_version(plain, tmp_path):
    _load(plain, tmp_path)
    _load(plain, tmp_path)
    ledger = _ledger(plain)
    versions = _versions(plain)
    assert len(ledger) == 2
    assert len(versions) == 1
    assert ledger[1]["status"] == UNCHANGED
    assert ledger[1]["version_uuid"] == versions[0]["uuid"]
    assert ledger[1]["uuid"] != versions[0]["uuid"]
    assert "status" not in ledger[0]


def test_repeated_reloads_all_name_the_same_version(plain, tmp_path):
    for _ in range(3):
        _load(plain, tmp_path)
    ledger = _ledger(plain)
    u1 = _versions(plain)[0]["uuid"]
    assert [e.get("status") for e in ledger] == [None, UNCHANGED, UNCHANGED]
    assert [e.get("version_uuid") for e in ledger] == [None, u1, u1]


def test_a_changed_reload_is_not_marked(plain, tmp_path):
    _load(plain, tmp_path)
    _load(plain, tmp_path, statement="$[*][no()]")
    ledger = _ledger(plain)
    assert len(_versions(plain)) == 2
    for entry in ledger:
        assert "status" not in entry
        assert "version_uuid" not in entry


def test_a_return_to_an_earlier_group_is_a_new_version(plain, tmp_path):
    #
    # only the most recent version is matched: A, B, A is three versions
    #
    _load(plain, tmp_path)
    _load(plain, tmp_path, statement="$[*][no()]")
    _load(plain, tmp_path)
    assert len(_versions(plain)) == 3
    assert [e.get("status") for e in _ledger(plain)] == [None, None, None]


def test_a_reload_names_the_most_recent_version(plain, tmp_path):
    #
    # A, B, B: the second B matches B, not A
    #
    _load(plain, tmp_path)
    _load(plain, tmp_path, statement="$[*][no()]")
    _load(plain, tmp_path, statement="$[*][no()]")
    versions = _versions(plain)
    assert len(versions) == 2
    assert _ledger(plain)[2]["status"] == UNCHANGED
    assert _ledger(plain)[2]["version_uuid"] == versions[1]["uuid"]


def test_an_unchanged_reload_leaves_the_per_name_manifest_alone(plain, tmp_path):
    _load(plain, tmp_path)
    before = json.dumps(_versions(plain))
    _load(plain, tmp_path)
    assert json.dumps(_versions(plain)) == before


def test_other_listeners_see_the_marked_metadata(plain, tmp_path):
    rec = _Recording(plain.config)
    plain.paths_manager.registrar.add_internal_listener(rec)
    _load(plain, tmp_path)
    _load(plain, tmp_path)
    assert len(rec.updates) == 2
    first, second = rec.updates
    assert first.status is None
    assert first.version_uuid is None
    assert second.status == UNCHANGED
    assert second.version_uuid == _versions(plain)[0]["uuid"]
    assert second.manifest_entry is None
    assert second.ledger_entry == _ledger(plain)[1]


def test_a_version_without_a_uuid_does_not_stop_a_reload(plain, tmp_path):
    #
    # an older per-name manifest entry with no uuid: the reload is still
    # marked, but has no version to name
    #
    _load(plain, tmp_path)
    versions = _versions(plain)
    del versions[0]["uuid"]
    plain.paths_manager.registrar.intermediary.put_json(
        _manifest_path(plain), versions
    )
    _load(plain, tmp_path)
    entry = _ledger(plain)[1]
    assert entry["status"] == UNCHANGED
    assert "version_uuid" not in entry


def test_the_registrar_reads_a_missing_version_uuid_without_raising(plain, tmp_path):
    #
    # directly, because distribute_update only logs the registrar's own
    # failures: a strict read would not be visible through a load
    #
    _load(plain, tmp_path)
    reg = plain.paths_manager.registrar
    versions = _versions(plain)
    del versions[0]["uuid"]
    reg.intermediary.put_json(_manifest_path(plain), versions)
    mdata = PathsMetadata(plain.config)
    mdata.named_paths_name = "orders"
    mdata.manifest_path = _manifest_path(plain)
    mdata.fingerprint = versions[0]["fingerprint"]
    reg.metadata_update(mdata)
    assert mdata.status == UNCHANGED
    assert mdata.version_uuid is None
    assert mdata.manifest_entry is None


# ===================
# SQL
# ===================


def test_sql_mirrors_an_unchanged_reload(sql, tmp_path):
    _load(sql, tmp_path)
    _load(sql, tmp_path)
    rows = _ledger_rows(sql)
    u1 = _versions(sql)[0]["uuid"]
    assert [json.loads(r["ledger_entry"]) for r in rows] == _ledger(sql)
    assert [r["ledger_index"] for r in rows] == [0, 1]
    assert [r["status"] for r in rows] == [None, UNCHANGED]
    assert [r["version_uuid"] for r in rows] == [u1, u1]
    assert rows[0]["uuid"] == u1
    assert rows[1]["uuid"] == _ledger(sql)[1]["uuid"]
    assert rows[1]["paths_name"] == "orders"


def test_sql_writes_no_version_for_an_unchanged_reload(sql, tmp_path):
    _load(sql, tmp_path)
    _load(sql, tmp_path)
    assert len(_rows(sql, sql="select uuid from named_paths")) == 1


def test_sql_changed_reloads_link_their_own_versions(sql, tmp_path):
    _load(sql, tmp_path)
    _load(sql, tmp_path, statement="$[*][no()]")
    rows = _ledger_rows(sql)
    assert [r["status"] for r in rows] == [None, None]
    assert [r["version_uuid"] for r in rows] == [r["uuid"] for r in rows]
    assert len(_rows(sql, sql="select uuid from named_paths")) == 2


def test_sql_a_version_without_a_uuid_gives_a_null_link(sql, tmp_path):
    _load(sql, tmp_path)
    versions = _versions(sql)
    del versions[0]["uuid"]
    sql.paths_manager.registrar.intermediary.put_json(_manifest_path(sql), versions)
    _load(sql, tmp_path)
    row = _ledger_rows(sql)[1]
    assert row["status"] == UNCHANGED
    assert row["version_uuid"] is None
