"""A named-file patch reaches every copy of the entry (harmonization PR 5).

FileRegistrar.patch_named_file goes through Registrar.distribute_patch:

  - the registrar patches the per-name entry, including its file_name,
    and appends the change to the entry's changes list:
    {"time", "change": "patch", "from": {the prior values of what changed}}
  - FilesListener patches the arrival's root ledger entry in place, and
    appends the same event in the ledger's own field names (file_path,
    not file)
  - SqlFileListener updates the named_file row, now including file_name,
    and the named_file_ledger row. Updates, not upserts, so the ledger
    row keeps the arrival's at and ledger_index.

A patch adds no entry anywhere. Every test uses its own roots and SQLite
file under pytest's tmp_path.
"""

import copy
import json
from datetime import datetime

import pytest
from sqlalchemy import text

from csvpath import CsvPaths
from csvpath.managers.files.file_metadata import FileMetadata
from csvpath.managers.files.files_listener import FilesListener
from csvpath.managers.integrations.sql.sql_file_listener import SqlFileListener
from csvpath.references.files_reference_finder_3 import FilesReferenceFinder3
from csvpath.references.reference_parser_3 import ReferenceParser3
from csvpath.util.box import Box


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
        value=f"sqlite:///{tmp_path / 'patch_ledger.db'}",
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


def _register(paths: CsvPaths, tmp_path, *, n: int = 0) -> None:
    data = tmp_path / f"orders_{n}.csv"
    data.write_text(f"id,amount\n{n},10\n", encoding="utf-8")
    paths.file_manager.add_named_file(name="orders", path=str(data))


def _patch(paths: CsvPaths, **kwargs) -> None:
    paths.file_manager.registrar.patch_named_file(name="orders", **kwargs)


def _manifest(paths: CsvPaths) -> list:
    #
    # a copy: the manifest can come back as a cached object
    #
    return copy.deepcopy(paths.file_manager.get_manifest("orders"))


def _ledger(paths: CsvPaths) -> list:
    return paths.file_manager.files_root_manifest or []


def _write_ledger(paths: CsvPaths, ledger: list) -> None:
    mpath = FilesListener(csvpaths=paths).manifest_path()
    with open(mpath, "w", encoding="utf-8") as file:
        json.dump(ledger, file, indent=2)


def _rows(paths: CsvPaths, *, sql: str) -> list[dict]:
    listener = SqlFileListener(config=paths.config)
    listener.csvpaths = paths
    with listener.engine.connect() as conn:
        return [dict(r._mapping) for r in conn.execute(text(sql))]


def _query(paths: CsvPaths, reference: str):
    ref = ReferenceParser3(string=reference, csvpaths=paths)
    return FilesReferenceFinder3(csvpaths=paths, ref=ref).query()


# ===================
# the per-name entry
# ===================


def test_file_metadata_change_defaults_to_none(plain):
    assert FileMetadata(plain.config).change is None


def test_a_file_name_patch_patches_the_entry_file_name(plain, tmp_path):
    _register(plain, tmp_path)
    _patch(plain, patch={"file_name": "orders_v2"})
    assert _manifest(plain)[0]["file_name"] == "orders_v2"


def test_a_patch_records_what_it_replaced(plain, tmp_path):
    _register(plain, tmp_path)
    before = _manifest(plain)[0]
    _patch(plain, patch={"type": "tsv", "file_name": "orders_v2"})
    entry = _manifest(plain)[0]
    assert len(entry["changes"]) == 1
    change = entry["changes"][0]
    assert change["change"] == "patch"
    assert change["from"] == {
        "type": before["type"],
        "file": before["file"],
        "file_home": before["file_home"],
        "file_name": before["file_name"],
    }
    datetime.fromisoformat(change["time"])


def test_a_type_patch_records_only_the_type(plain, tmp_path):
    _register(plain, tmp_path)
    _patch(plain, patch={"type": "tsv"})
    assert _manifest(plain)[0]["changes"][0]["from"] == {"type": "csv"}


def test_patches_accumulate_in_order(plain, tmp_path):
    _register(plain, tmp_path)
    _patch(plain, patch={"type": "tsv"})
    _patch(plain, patch={"type": "psv"})
    changes = _manifest(plain)[0]["changes"]
    assert [c["from"] for c in changes] == [{"type": "csv"}, {"type": "tsv"}]


def test_an_unpatched_entry_has_no_changes(plain, tmp_path):
    _register(plain, tmp_path)
    assert "changes" not in _manifest(plain)[0]
    assert "changes" not in _ledger(plain)[0]


# ===================
# the ledger entry
# ===================


def test_a_patch_patches_the_ledger_entry_in_place(plain, tmp_path):
    _register(plain, tmp_path)
    _patch(plain, patch={"type": "tsv", "file_name": "orders_v2"})
    entry = _manifest(plain)[0]
    ledger = _ledger(plain)
    assert len(ledger) == 1
    assert ledger[0]["uuid"] == entry["uuid"]
    assert ledger[0]["type"] == "tsv"
    assert ledger[0]["file_path"] == entry["file"]
    assert ledger[0]["file_home"] == entry["file_home"]
    assert ledger[0]["file_name"] == "orders_v2"


def test_the_ledger_records_the_change_in_its_own_names(plain, tmp_path):
    _register(plain, tmp_path)
    before = copy.deepcopy(_ledger(plain)[0])
    _patch(plain, patch={"type": "tsv", "file_name": "orders_v2"})
    per_name = _manifest(plain)[0]["changes"][0]
    change = _ledger(plain)[0]["changes"][0]
    assert change["from"] == {
        "type": before["type"],
        "file_path": before["file_path"],
        "file_home": before["file_home"],
        "file_name": before["file_name"],
    }
    assert change["time"] == per_name["time"]
    assert change["change"] == "patch"


def test_a_type_patch_records_only_the_type_in_the_ledger(plain, tmp_path):
    _register(plain, tmp_path)
    _patch(plain, patch={"type": "tsv"})
    assert _ledger(plain)[0]["changes"][0]["from"] == {"type": "csv"}


def test_an_indexed_patch_patches_that_ledger_entry(plain, tmp_path):
    _register(plain, tmp_path, n=0)
    _register(plain, tmp_path, n=1)
    _patch(plain, patch={"type": "tsv"}, index=0)
    ledger = _ledger(plain)
    assert ledger[0]["type"] == "tsv"
    assert ledger[1]["type"] == "csv"
    assert "changes" not in ledger[1]


def test_the_arrival_is_patched_not_a_failure_with_its_uuid(plain, tmp_path):
    #
    # ledgers from before failures had their own uuid can hold a failure
    # with the arrival's uuid; it has no file_path
    #
    _register(plain, tmp_path)
    ledger = _ledger(plain)
    failure = {
        "uuid": ledger[0]["uuid"],
        "named_file_name": "orders",
        "file_path": None,
        "status": "failed",
    }
    _write_ledger(plain, [failure] + ledger)
    _patch(plain, patch={"type": "tsv"})
    ledger = _ledger(plain)
    assert "changes" not in ledger[0]
    assert ledger[1]["type"] == "tsv"


def test_a_missing_ledger_entry_is_not_backfilled(plain, tmp_path):
    _register(plain, tmp_path)
    _write_ledger(plain, [])
    _patch(plain, patch={"type": "tsv"})
    assert _ledger(plain) == []
    assert _manifest(plain)[0]["type"] == "tsv"


def test_the_ledger_writer_sets_the_patched_entry_and_position(plain, tmp_path):
    _register(plain, tmp_path, n=0)
    _register(plain, tmp_path, n=1)
    mdata = FileMetadata(plain.config)
    mdata.manifest_entry = {"uuid": _ledger(plain)[1]["uuid"], "type": "tsv"}
    mdata.change = {"time": "t", "change": "patch", "from": {}}
    FilesListener(csvpaths=plain).metadata_patch(mdata)
    assert mdata.ledger_index == 1
    assert mdata.ledger_entry == _ledger(plain)[1]


def test_the_ledger_writer_requires_a_patched_entry(plain):
    lst = FilesListener(csvpaths=plain)
    with pytest.raises(ValueError):
        lst.metadata_patch(None)
    mdata = FileMetadata(plain.config)
    with pytest.raises(ValueError):
        lst.metadata_patch(mdata)
    mdata.manifest_entry = {"uuid": "u"}
    with pytest.raises(ValueError):
        lst.metadata_patch(mdata)


@pytest.mark.parametrize("uuid", [None, "", "  ", 3])
def test_arrival_index_rejects_bad_uuids(plain, uuid):
    with pytest.raises(ValueError):
        FilesListener(csvpaths=plain)._arrival_index(jdata=[], uuid=uuid)


# ===================
# v3 reads
# ===================


def test_a_star_read_returns_the_patched_path(plain, tmp_path):
    _register(plain, tmp_path)
    old = _ledger(plain)[0]["file_path"]
    _patch(plain, patch={"type": "tsv", "file_name": "orders_v2"})
    r = _query(plain, "$*.files.:manifest():uuid()")
    assert r.files == [_manifest(plain)[0]["file"]]
    assert old not in r.files


# ===================
# SQL
# ===================


def test_sql_named_file_file_name_is_patched(sql, tmp_path):
    _register(sql, tmp_path)
    _patch(sql, patch={"file_name": "orders_v2"})
    rows = _rows(sql, sql="select file_name, manifest_entry from named_file")
    assert rows[0]["file_name"] == "orders_v2"
    assert json.loads(rows[0]["manifest_entry"]) == _manifest(sql)[0]


def test_sql_ledger_row_equals_the_patched_entry(sql, tmp_path):
    _register(sql, tmp_path)
    before = _rows(sql, sql="select * from named_file_ledger")[0]
    _patch(sql, patch={"type": "tsv", "file_name": "orders_v2"})
    rows = _rows(sql, sql="select * from named_file_ledger")
    assert len(rows) == 1
    assert json.loads(rows[0]["ledger_entry"]) == _ledger(sql)[0]
    assert rows[0]["at"] == before["at"]
    assert rows[0]["ledger_index"] == before["ledger_index"]
    assert rows[0]["status"] == "complete"


def test_sql_a_missing_ledger_row_is_not_backfilled(sql, tmp_path):
    _register(sql, tmp_path)
    listener = SqlFileListener(config=sql.config)
    listener.csvpaths = sql
    with listener.engine.connect() as conn:
        conn.execute(text("delete from named_file_ledger"))
        conn.commit()
    _patch(sql, patch={"type": "tsv"})
    assert _rows(sql, sql="select * from named_file_ledger") == []


def test_sql_no_patched_ledger_entry_means_no_ledger_update(sql, tmp_path):
    _register(sql, tmp_path)
    before = _rows(sql, sql="select ledger_entry from named_file_ledger")
    _write_ledger(sql, [])
    _patch(sql, patch={"type": "tsv"})
    assert _rows(sql, sql="select ledger_entry from named_file_ledger") == before


@pytest.mark.parametrize(
    "kwargs",
    [
        {"table": None, "uuid": "u", "values": {"a": 1}},
        {"uuid": "", "values": {"a": 1}},
        {"uuid": None, "values": {"a": 1}},
        {"uuid": "u", "values": {}},
        {"uuid": "u", "values": None},
    ],
)
def test_update_by_uuid_rejects_bad_arguments(sql, kwargs):
    listener = SqlFileListener(config=sql.config)
    listener.csvpaths = sql
    args = {"table": listener.named_file_ledger}
    args.update(kwargs)
    with pytest.raises(ValueError):
        listener._update_by_uuid_unreliably(**args)
