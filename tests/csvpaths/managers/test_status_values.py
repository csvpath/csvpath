"""Every root ledger entry has a status (harmonization PR 4.5). None is
implied by absence.

- FILES: "complete" for an arrival, "failed" for a failed registration
  (formerly "Registration failed").
- CSVPATHS: "complete" for a load that writes a version, "unchanged" for
  an unchanged reload (PR 4).

"complete" is the same string RESULTS writes, so :status("complete")
means the same thing for every datatype. Older entries with no status are
not migrated and match no :status() value.

Every test uses its own roots and SQLite file under pytest's tmp_path.
"""

import json

import pytest
from sqlalchemy import text

from csvpath import CsvPaths
from csvpath.managers.files.file_metadata import FileMetadata
from csvpath.managers.files.files_listener import FilesListener
from csvpath.managers.integrations.sql.sql_file_listener import SqlFileListener
from csvpath.managers.paths.paths_listener import PathsListener
from csvpath.managers.paths.paths_metadata import PathsMetadata
from csvpath.managers.registrar import Registrar
from csvpath.managers.results.results_registrar import ResultsRegistrar
from csvpath.references.files_reference_finder_3 import FilesReferenceFinder3
from csvpath.references.reference_parser_3 import ReferenceParser3
from csvpath.util.box import Box

COMPLETE = "complete"
FAILED = "failed"


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
        value=f"sqlite:///{tmp_path / 'status.db'}",
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


def _fail(paths: CsvPaths) -> None:
    with pytest.raises(ValueError):
        paths.file_manager.add_named_file(name="orders", path="")


def _load(paths: CsvPaths, tmp_path) -> None:
    f = tmp_path / "orders.csvpaths"
    f.write_text("$[*][yes()]", encoding="utf-8")
    paths.paths_manager.add_named_paths_from_file(name="orders", file_path=str(f))


def _files_ledger(paths: CsvPaths) -> list:
    return paths.file_manager.files_root_manifest or []


def _paths_ledger(paths: CsvPaths) -> list:
    return paths.paths_manager.paths_root_manifest or []


def _rows(paths: CsvPaths, *, sql: str) -> list[dict]:
    listener = SqlFileListener(config=paths.config)
    listener.csvpaths = paths
    with listener.engine.connect() as conn:
        return [dict(r._mapping) for r in conn.execute(text(sql))]


def _query(paths: CsvPaths, reference: str):
    ref = ReferenceParser3(string=reference, csvpaths=paths)
    return FilesReferenceFinder3(csvpaths=paths, ref=ref).query()


# ===================
# the values
# ===================


def test_the_status_values(plain):
    assert Registrar.COMPLETE == COMPLETE
    assert Registrar.FAILED == FAILED


def test_complete_is_the_results_value(plain):
    assert Registrar.COMPLETE == ResultsRegistrar.COMPLETE


def test_file_metadata_status_defaults_to_none(plain):
    assert FileMetadata(plain.config).status is None


# ===================
# FILES
# ===================


def test_an_arrival_is_complete(plain, tmp_path):
    _register(plain, tmp_path)
    assert _files_ledger(plain)[0]["status"] == COMPLETE


def test_a_failure_is_failed(plain):
    _fail(plain)
    assert _files_ledger(plain)[0]["status"] == FAILED


def test_every_files_entry_has_a_status(plain, tmp_path):
    _register(plain, tmp_path, n=0)
    _fail(plain)
    _register(plain, tmp_path, n=1)
    assert [e["status"] for e in _files_ledger(plain)] == [COMPLETE, FAILED, COMPLETE]


def test_a_duplicate_arrival_still_writes_nothing(plain, tmp_path):
    _register(plain, tmp_path)
    _register(plain, tmp_path)
    assert len(_files_ledger(plain)) == 1


def test_the_per_name_manifest_has_no_status(plain, tmp_path):
    _register(plain, tmp_path)
    for entry in plain.file_manager.get_manifest("orders"):
        assert "status" not in entry


def test_the_files_ledger_writer_requires_a_status(plain):
    mdata = FileMetadata(plain.config)
    mdata.named_file_name = "orders"
    with pytest.raises(ValueError, match="requires a status"):
        FilesListener(csvpaths=plain)._prep_update(mdata)


# ===================
# CSVPATHS
# ===================


def test_a_load_is_complete(plain, tmp_path):
    _load(plain, tmp_path)
    assert _paths_ledger(plain)[0]["status"] == COMPLETE


def test_the_paths_ledger_writer_requires_a_status(plain):
    mdata = PathsMetadata(plain.config)
    mdata.named_paths_name = "orders"
    with pytest.raises(ValueError, match="requires a status"):
        PathsListener(csvpaths=plain)._prep_update(mdata)


# ===================
# SQL
# ===================


def test_sql_files_rows_carry_the_status(sql, tmp_path):
    _register(sql, tmp_path)
    _fail(sql)
    rows = _rows(sql, sql="select * from named_file_ledger order by ledger_index")
    assert [r["status"] for r in rows] == [COMPLETE, FAILED]
    assert [json.loads(r["ledger_entry"])["status"] for r in rows] == [
        COMPLETE,
        FAILED,
    ]


def test_sql_paths_rows_carry_the_status(sql, tmp_path):
    _load(sql, tmp_path)
    rows = _rows(sql, sql="select status from named_paths_ledger")
    assert rows == [{"status": COMPLETE}]


# ===================
# v3 reads
# ===================


def test_status_complete_selects_arrivals(plain, tmp_path):
    _register(plain, tmp_path, n=0)
    _fail(plain)
    _register(plain, tmp_path, n=1)
    ledger = _files_ledger(plain)
    r = _query(plain, '$*.files.:status("complete")')
    assert r.files == [ledger[0]["file_path"], ledger[2]["file_path"]]


def test_status_failed_selects_failures(plain, tmp_path):
    _register(plain, tmp_path)
    _fail(plain)
    r = _query(plain, '$*.files.:status("failed")')
    assert len(r.files) == 1


def test_an_entry_without_a_status_matches_neither(plain, tmp_path):
    #
    # an entry written before every entry had a status: not migrated, and
    # absence means nothing
    #
    _register(plain, tmp_path)
    ledger = _files_ledger(plain)
    old = dict(ledger[0])
    del old["status"]
    old["uuid"] = "old-1"
    ledger.insert(0, old)
    mpath = FilesListener(csvpaths=plain).manifest_path()
    with open(mpath, "w", encoding="utf-8") as file:
        json.dump(ledger, file, indent=2)
    complete = _query(plain, '$*.files.:status("complete")')
    assert complete.files == [ledger[1]["file_path"]]
    assert len(_query(plain, '$*.files.:status("failed")').files) == 0
