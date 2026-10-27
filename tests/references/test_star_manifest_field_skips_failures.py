"""`$*.files.:manifest():<field>()` returns the file_path of every arrival in
the named-files root ledger. A failed registration is in the ledger too,
but has no file: its file_path is None, or missing altogether in ledgers
from before the ledger writers were built in. Those entries are skipped,
whatever their status says. They used to raise a ValueError from
ReferenceResult3.

Every test uses its own roots under pytest's tmp_path.
"""

import json

import pytest

from csvpath import CsvPaths
from csvpath.managers.files.files_listener import FilesListener
from csvpath.references.files_reference_finder_3 import FilesReferenceFinder3
from csvpath.references.reference_parser_3 import ReferenceParser3
from csvpath.util.box import Box

STAR = "$*.files.:manifest():uuid()"


def _clear_engine() -> None:
    box = Box()
    e = box.get(key=Box.SQL_ENGINE)
    if e is not None:
        e.dispose()
        box.remove(Box.SQL_ENGINE)


def _paths(tmp_path, *, groups: str = "") -> CsvPaths:
    p = CsvPaths()
    c = p.config
    c.add_to_config(section="inputs", key="files", value=str(tmp_path / "named_files"))
    c.add_to_config(section="inputs", key="csvpaths", value=str(tmp_path / "named_paths"))
    c.add_to_config(section="results", key="archive", value=str(tmp_path / "archive"))
    c.add_to_config(section="listeners", key="groups", value=groups)
    c.add_to_config(section="sql", key="dialect", value="sqlite")
    c.add_to_config(
        section="sql", key="connection_string", value=f"sqlite:///{tmp_path / 'f.db'}"
    )
    return p


@pytest.fixture
def paths(tmp_path):
    _clear_engine()
    yield _paths(tmp_path)
    _clear_engine()


def _register(p: CsvPaths, tmp_path, *, name: str = "orders", n: int = 0) -> None:
    data = tmp_path / f"{name}_{n}.csv"
    data.write_text(f"id,amount\n{n},10\n", encoding="utf-8")
    p.file_manager.add_named_file(name=name, path=str(data))


def _fail(p: CsvPaths, *, name: str = "orders") -> None:
    with pytest.raises(ValueError):
        p.file_manager.add_named_file(name=name, path="")


def _ledger(p: CsvPaths) -> list:
    return p.file_manager.files_root_manifest or []


def _write_ledger(p: CsvPaths, ledger: list) -> None:
    with open(FilesListener(csvpaths=p).manifest_path(), "w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=2)


def _query(p: CsvPaths, reference: str = STAR):
    ref = ReferenceParser3(string=reference, csvpaths=p)
    return FilesReferenceFinder3(csvpaths=p, ref=ref).query()


def _arrivals(p: CsvPaths) -> list[tuple]:
    return [(e["file_path"], e["uuid"]) for e in _ledger(p) if e.get("file_path")]


def _results(r) -> list[tuple]:
    return [(x.path, x.uuid) for x in r.results]


def test_a_failure_is_skipped(paths, tmp_path):
    _register(paths, tmp_path, n=0)
    _fail(paths)
    _register(paths, tmp_path, n=1)
    assert [e["status"] for e in _ledger(paths)] == ["complete", "failed", "complete"]
    assert _ledger(paths)[1]["file_path"] is None
    r = _query(paths)
    assert len(r) == 2
    assert _results(r) == _arrivals(paths)


def test_an_old_failure_with_no_file_path_key_is_skipped(paths, tmp_path):
    _register(paths, tmp_path)
    ledger = _ledger(paths)
    ledger.append(
        {
            "named_file_name": "orders",
            "origin_path": "",
            "status": "Registration failed",
            "uuid": "old-failure",
        }
    )
    _write_ledger(paths, ledger)
    r = _query(paths)
    assert _results(r) == [(ledger[0]["file_path"], ledger[0]["uuid"])]


def test_an_empty_file_path_is_skipped(paths, tmp_path):
    _register(paths, tmp_path)
    ledger = _ledger(paths)
    ledger.append(dict(ledger[0], uuid="empty", file_path=""))
    _write_ledger(paths, ledger)
    assert [x.uuid for x in _query(paths).results] == [ledger[0]["uuid"]]


def test_a_ledger_of_only_failures_is_empty(paths):
    _fail(paths)
    _fail(paths, name="people")
    assert len(_query(paths)) == 0


def test_the_name_filter_still_applies(paths, tmp_path):
    _register(paths, tmp_path, name="orders")
    _register(paths, tmp_path, name="people")
    _fail(paths, name="orders")
    r = _query(paths, "$:regex(/^o/).files.:manifest():uuid()")
    assert [x.uuid for x in r.results] == [_ledger(paths)[0]["uuid"]]


def test_deleted_arrivals_are_still_returned(paths, tmp_path):
    #
    # ledger reads keep deleted entries until a :lifecycle() gate
    #
    _register(paths, tmp_path)
    _fail(paths)
    paths.file_manager.remove_named_file("orders")
    assert _results(_query(paths)) == _arrivals(paths)
    assert len(_query(paths)) == 1


def test_sql_on_skips_failures_the_same_way(tmp_path):
    _clear_engine()
    p = _paths(tmp_path, groups="sql")
    try:
        _register(p, tmp_path, n=0)
        _fail(p)
        off = _query(p)
        p.config.add_to_config(section="references", key="sql", value="on")
        on = _query(p)
        assert len(on) == 1
        assert on == off
    finally:
        p.config.add_to_config(section="references", key="sql", value="off")
        _clear_engine()
