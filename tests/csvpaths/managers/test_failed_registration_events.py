"""Failed named-file registrations are events (harmonization PR 3).
FileManager._registration_failed sends them through
Registrar.distribute_failure, which calls each listener's
metadata_failure. The default is to ignore a failure, so listeners that
report registrations (OTLP, OpenLineage, Slack, ...) are unchanged. The
root ledger writer records it and the SQL listener mirrors that entry.

A failure has its own uuid. The attempt's uuid is kept as
registration_uuid: when a registration fails after its arrival entry was
written, the two entries no longer share a uuid.

Every test uses its own roots and SQLite file under pytest's tmp_path.
"""

import json

import pytest
from sqlalchemy import inspect, text

from csvpath import CsvPaths
from csvpath.managers.files.file_metadata import FileMetadata
from csvpath.managers.files.files_listener import FilesListener
from csvpath.managers.integrations.sql.sql_file_listener import SqlFileListener
from csvpath.managers.integrations.sql.sql_listener import SqlListener
from csvpath.managers.listener import Listener
from csvpath.util.box import Box
from csvpath.util.exceptions import RequiredListenerException

NO_RAISE_POLICY = "collect, print"
FAILED = "Registration failed"


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
        value=f"sqlite:///{tmp_path / 'failed.db'}",
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


def _ledger(paths: CsvPaths) -> list:
    return paths.file_manager.files_root_manifest or []


def _rows(paths: CsvPaths, *, sql: str) -> list[dict]:
    listener = SqlFileListener(config=paths.config)
    listener.csvpaths = paths
    with listener.engine.connect() as conn:
        return [dict(r._mapping) for r in conn.execute(text(sql))]


def _register(paths: CsvPaths, tmp_path, *, n: int = 0) -> None:
    data = tmp_path / f"orders_{n}.csv"
    data.write_text(f"id,amount\n{n},10\n", encoding="utf-8")
    paths.file_manager.add_named_file(name="orders", path=str(data))


def _fail_early(paths: CsvPaths) -> None:
    with pytest.raises(ValueError):
        paths.file_manager.add_named_file(name="orders", path="")


def _failure(*, name="orders", registration_uuid="r-1") -> dict:
    return {
        "name": name,
        "path": "/nowhere/orders.csv",
        "template": None,
        "registration_uuid": registration_uuid,
    }


class _Recording(Listener):
    """records the updates and failures it is sent"""

    def __init__(self, config=None, *, read=None) -> None:
        super().__init__(config)
        self.read = read
        self.updates = []
        self.failures = []
        self.ledger_lengths = []

    def metadata_update(self, mdata) -> None:
        self.updates.append(mdata)

    def metadata_failure(self, mdata) -> None:
        self.failures.append(mdata)
        if self.read is not None:
            self.ledger_lengths.append(len(self.read()))


class _Reporter(Listener):
    """a configured listener that only reports registrations, like the
    OTLP, OpenLineage and Slack listeners"""

    seen = []

    def metadata_update(self, mdata) -> None:
        _Reporter.seen.append(mdata)


class _RaisingAfterArrival(Listener):
    """fails a registration after the ledger writer has run"""

    def metadata_update(self, mdata) -> None:
        raise RuntimeError("downstream listener failed")

    def raise_on_update_error(self) -> bool:
        return True


# ===================
# the hooks
# ===================


def test_listener_ignores_failures_by_default(plain):
    assert _Reporter(plain.config).metadata_failure(FileMetadata(plain.config)) is None


def test_file_metadata_registration_uuid_defaults_to_none(plain):
    assert FileMetadata(plain.config).registration_uuid is None


def test_distribute_failure_rejects_none(plain):
    with pytest.raises(Exception, match="Metadata cannot be None"):
        plain.file_manager.registrar.distribute_failure(None)


@pytest.mark.parametrize("method", [None, "", "  ", 3])
def test_listeners_with_rejects_bad_methods(plain, method):
    with pytest.raises(ValueError):
        plain.file_manager.registrar._listeners_with(method=method)


def test_listeners_with_keeps_distribution_order(plain):
    rec = _Recording(plain.config)
    reg = plain.file_manager.registrar
    reg.add_internal_listener(rec)
    found = reg._listeners_with(method="metadata_failure")
    assert [type(lst) for lst, _ in found] == [
        type(reg),
        FilesListener,
        _Recording,
    ]
    assert found[2][1] == rec.metadata_failure


# ===================
# the failure entry
# ===================


def test_an_early_failure_gets_its_own_uuid(plain):
    plain.file_manager._registration_failed(_failure(registration_uuid="r-1"))
    ledger = _ledger(plain)
    assert len(ledger) == 1
    assert ledger[0]["status"] == FAILED
    assert ledger[0]["registration_uuid"] == "r-1"
    assert ledger[0]["uuid"] != "r-1"
    assert ledger[0]["named_file_name"] == "orders"
    assert ledger[0]["origin_path"] == "/nowhere/orders.csv"


def test_an_empty_path_records_one_failure(plain):
    _fail_early(plain)
    ledger = _ledger(plain)
    assert len(ledger) == 1
    assert ledger[0]["status"] == FAILED
    assert ledger[0]["uuid"] != ledger[0]["registration_uuid"]


def test_a_late_failure_does_not_reuse_the_arrival_uuid(plain, tmp_path):
    plain.file_manager.registrar.add_internal_listener(
        _RaisingAfterArrival(plain.config)
    )
    with pytest.raises(RuntimeError, match="downstream listener failed"):
        _register(plain, tmp_path)
    ledger = _ledger(plain)
    assert len(ledger) == 2
    assert "status" not in ledger[0]
    assert ledger[1]["status"] == FAILED
    assert ledger[0]["uuid"] != ledger[1]["uuid"]
    assert ledger[1]["registration_uuid"] == ledger[0]["uuid"]


def test_ledger_uuids_are_unique_over_mixed_events(plain, tmp_path):
    _register(plain, tmp_path, n=0)
    _fail_early(plain)
    _register(plain, tmp_path, n=1)
    _fail_early(plain)
    uuids = [e["uuid"] for e in _ledger(plain)]
    assert len(uuids) == 4
    assert len(set(uuids)) == 4


def test_arrivals_have_no_registration_uuid(plain, tmp_path):
    _register(plain, tmp_path)
    assert "registration_uuid" not in _ledger(plain)[0]


@pytest.mark.parametrize("name", [None, "", "   "])
def test_a_failure_without_a_name_is_unknown(plain, name):
    plain.file_manager._registration_failed(_failure(name=name))
    assert _ledger(plain)[0]["named_file_name"] == "<unknown>"


def test_a_failure_name_is_a_str(plain):
    plain.file_manager._registration_failed(_failure(name=7))
    assert _ledger(plain)[0]["named_file_name"] == "7"


# ===================
# distribution
# ===================


def test_the_ledger_is_written_before_other_listeners_see_the_failure(plain):
    rec = _Recording(plain.config, read=lambda: _ledger(plain))
    plain.file_manager.registrar.add_internal_listener(rec)
    plain.file_manager._registration_failed(_failure())
    assert rec.updates == []
    assert len(rec.failures) == 1
    assert rec.ledger_lengths == [1]
    assert rec.failures[0].ledger_entry == _ledger(plain)[0]
    assert rec.failures[0].ledger_index == 0


def test_a_failure_leaves_the_per_name_manifest_alone(plain, tmp_path):
    _register(plain, tmp_path)
    before = json.dumps(plain.file_manager.get_manifest("orders"))
    _fail_early(plain)
    assert json.dumps(plain.file_manager.get_manifest("orders")) == before


def test_reporting_listeners_are_not_sent_failures(tmp_path):
    _clear_engine()
    p = _paths(tmp_path, groups="mine")
    p.config.add_to_config(
        section="listeners", key="mine.file", value=f"from {__name__} import _Reporter"
    )
    _Reporter.seen = []
    try:
        _fail_early(p)
        assert _Reporter.seen == []
        _register(p, tmp_path)
        assert len(_Reporter.seen) == 1
    finally:
        _clear_engine()


# ===================
# SQL
# ===================


def test_sql_mirrors_the_failure_entry(sql):
    sql.file_manager._registration_failed(_failure(registration_uuid="r-1"))
    rows = _rows(sql, sql="select * from named_file_ledger")
    assert len(rows) == 1
    assert json.loads(rows[0]["ledger_entry"]) == _ledger(sql)[0]
    assert rows[0]["uuid"] == _ledger(sql)[0]["uuid"]
    assert rows[0]["status"] == FAILED
    assert rows[0]["version_uuid"] is None
    assert rows[0]["ledger_index"] == 0
    assert rows[0]["named_file_name"] == "orders"


def test_sql_has_no_version_for_a_failure(sql):
    _fail_early(sql)
    assert len(_rows(sql, sql="select * from named_file_ledger")) == 1
    insp = inspect(SqlFileListener(config=sql.config).engine)
    if insp.has_table("named_file"):
        assert _rows(sql, sql="select * from named_file") == []


def test_sql_ledger_rows_equal_the_json_ledger_over_mixed_events(sql, tmp_path):
    _register(sql, tmp_path, n=0)
    _fail_early(sql)
    _register(sql, tmp_path, n=1)
    rows = _rows(sql, sql="select * from named_file_ledger order by ledger_index")
    assert [json.loads(r["ledger_entry"]) for r in rows] == _ledger(sql)
    assert [r["ledger_index"] for r in rows] == [0, 1, 2]
    assert [r["status"] for r in rows] == [None, FAILED, None]
    assert rows[1]["version_uuid"] is None
    assert rows[0]["version_uuid"] == rows[0]["uuid"]


def test_sql_records_an_unknown_name(sql):
    sql.file_manager._registration_failed(_failure(name=None))
    rows = _rows(sql, sql="select named_file_name from named_file_ledger")
    assert rows == [{"named_file_name": "<unknown>"}]


@pytest.mark.parametrize("policy", ["raise, collect, print", NO_RAISE_POLICY])
def test_a_failed_failure_row_raises_required_under_on(sql, policy, monkeypatch):
    sql.config.add_to_config(section="errors", key="csvpaths", value=policy)
    sql.config.add_to_config(section="references", key="sql", value="on")

    def fail(self, *, table, row):
        raise RuntimeError("ledger row failed")

    monkeypatch.setattr(SqlListener, "_upsert_ledger_row_unreliably", fail)
    with pytest.raises(RequiredListenerException, match="SqlFileListener"):
        sql.file_manager._registration_failed(_failure())
    assert _ledger(sql)[0]["status"] == FAILED


def test_a_failed_failure_row_is_logged_under_off_without_raise_policy(
    sql, monkeypatch
):
    sql.config.add_to_config(section="errors", key="csvpaths", value=NO_RAISE_POLICY)

    def fail(self, *, table, row):
        raise RuntimeError("ledger row failed")

    monkeypatch.setattr(SqlListener, "_upsert_ledger_row_unreliably", fail)
    sql.file_manager._registration_failed(_failure())
    assert len(_ledger(sql)) == 1


def test_sql_failure_hook_needs_csvpaths(sql):
    with pytest.raises(RuntimeError):
        SqlFileListener(config=sql.config).metadata_failure(FileMetadata(sql.config))
