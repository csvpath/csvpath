"""SqlReferenceSource reads FILES and CSVPATHS reference metadata from the
SQL listeners' tables when [references] sql = on (step 4b), and
CsvPaths.reference_source chooses between it and the filesystem.

  - per-name manifests: manifest_entry, active rows, by manifest_index
  - root ledgers: ledger_entry, every row (deleted ones kept), by
    ledger_index
  - names: active names, sorted the same way as the filesystem source
  - everything scoped to the configured roots
  - RESULTS still from the filesystem (step 4c)

Each test uses its own roots and SQLite file under pytest's tmp_path.
"""

import json
import shutil

import pytest
from sqlalchemy import text

from csvpath import CsvPaths
from csvpath.managers.integrations.sql.references_sql_check import (
    ReferencesSqlCheck,
)
from csvpath.references.reference_finder_factory_3 import ReferenceFinderFactory3
from csvpath.references.sources.filesystem_reference_source import (
    FilesystemReferenceSource,
)
from csvpath.references.sources.reference_source import ReferenceSource
from csvpath.references.sources.sql_reference_source import SqlReferenceSource
from csvpath.util.box import Box
from csvpath.util.config_exception import ConfigurationException
from csvpath.util.nos import Nos


def _clear_engine() -> None:
    box = Box()
    e = box.get(key=Box.SQL_ENGINE)
    if e is not None:
        e.dispose()
        box.remove(Box.SQL_ENGINE)


def _paths(tmp_path, *, root: str = "a", groups: str = "sql") -> CsvPaths:
    p = CsvPaths()
    c = p.config
    c.add_to_config(section="inputs", key="files", value=str(tmp_path / root / "nf"))
    c.add_to_config(
        section="inputs", key="csvpaths", value=str(tmp_path / root / "np")
    )
    c.add_to_config(section="results", key="archive", value=str(tmp_path / root / "ar"))
    c.add_to_config(section="listeners", key="groups", value=groups)
    c.add_to_config(section="sql", key="dialect", value="sqlite")
    c.add_to_config(
        section="sql",
        key="connection_string",
        value=f"sqlite:///{tmp_path / 'source.db'}",
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


def _load(p: CsvPaths, tmp_path, *, name: str = "orders", n: int = 0) -> None:
    f = tmp_path / f"{name}.csvpaths"
    f.write_text(f"~ id: s{n} ~ $[*][yes()]", encoding="utf-8")
    p.paths_manager.add_named_paths_from_file(name=name, file_path=str(f))


def _sql(p: CsvPaths) -> SqlReferenceSource:
    return SqlReferenceSource(csvpaths=p)


def _fs(p: CsvPaths) -> FilesystemReferenceSource:
    return FilesystemReferenceSource(csvpaths=p)


def _execute(p: CsvPaths, sql: str) -> None:
    with _sql(p).engine.connect() as conn:
        conn.execute(text(sql))
        conn.commit()


# ===================
# construction
# ===================


def test_is_a_reference_source(paths):
    s = _sql(paths)
    assert isinstance(s, ReferenceSource)
    assert isinstance(s, FilesystemReferenceSource)


def test_csvpaths_cannot_be_none():
    with pytest.raises(ValueError):
        SqlReferenceSource(csvpaths=None)


@pytest.mark.parametrize("method", ["file_manifest", "paths_manifest"])
@pytest.mark.parametrize("bad,error", [(None, ValueError), ("", ValueError), (1, TypeError)])
def test_bad_names_raise(paths, method, bad, error):
    with pytest.raises(error):
        getattr(_sql(paths), method)(bad)


@pytest.mark.parametrize(
    "method",
    ["results_ledger", "run_homes", "run_manifest", "instance_manifest", "instance_dirs"],
)
def test_results_reads_are_its_own(method):
    #
    # 4c-2; they were inherited from the filesystem source in 4b
    #
    assert getattr(SqlReferenceSource, method) is not getattr(
        FilesystemReferenceSource, method
    )


@pytest.mark.parametrize("method", ["run_manifest", "instance_manifest", "instance_dirs"])
@pytest.mark.parametrize("bad,error", [(None, ValueError), ("", ValueError), (1, TypeError)])
def test_bad_results_dirs_raise(paths, method, bad, error):
    with pytest.raises(error):
        getattr(_sql(paths), method)(bad)


# ===================
# the same as the filesystem
# ===================


def test_files_reads_equal_the_filesystem(paths, tmp_path):
    _register(paths, tmp_path, n=0)
    _register(paths, tmp_path, n=1)
    _register(paths, tmp_path, name="people")
    with pytest.raises(ValueError):
        paths.file_manager.add_named_file(name="orders", path="")
    sql, fs = _sql(paths), _fs(paths)
    assert sql.file_manifest("orders") == fs.file_manifest("orders")
    assert len(sql.file_manifest("orders")) == 2
    assert sql.files_ledger() == fs.files_ledger()
    assert len(sql.files_ledger()) == 4
    assert sql.file_names() == fs.file_names() == ["orders", "people"]


def test_paths_reads_equal_the_filesystem(paths, tmp_path):
    _load(paths, tmp_path, n=0)
    _load(paths, tmp_path, n=0)
    _load(paths, tmp_path, n=1)
    _load(paths, tmp_path, name="beta")
    sql, fs = _sql(paths), _fs(paths)
    assert sql.paths_manifest("orders") == fs.paths_manifest("orders")
    assert len(sql.paths_manifest("orders")) == 2
    assert sql.paths_ledger() == fs.paths_ledger()
    assert [e["status"] for e in sql.paths_ledger()] == [
        "complete",
        "unchanged",
        "complete",
        "complete",
    ]
    assert sql.paths_names() == fs.paths_names() == ["beta", "orders"]


def test_patched_entries_are_read_as_patched(paths, tmp_path):
    _register(paths, tmp_path)
    paths.file_manager.registrar.patch_named_file(name="orders", patch={"type": "tsv"})
    assert _sql(paths).file_manifest("orders")[0]["type"] == "tsv"
    assert _sql(paths).files_ledger()[0]["type"] == "tsv"
    assert _sql(paths).file_manifest("orders") == _fs(paths).file_manifest("orders")


def test_an_empty_ledger_is_an_empty_list(paths):
    assert _sql(paths).files_ledger() == []
    assert _sql(paths).paths_ledger() == []
    assert _sql(paths).file_names() == []
    assert _sql(paths).paths_names() == []


# ===================
# it reads SQL, not the JSON
# ===================


def test_reads_come_from_sql(paths, tmp_path):
    _register(paths, tmp_path)
    _load(paths, tmp_path)
    expected = _sql(paths).file_manifest("orders")
    home = paths.file_manager.named_file_home("orders")
    Nos(Nos(home).join("manifest.json")).remove()
    Nos(paths.file_manager.files_root_manifest_path).remove()
    Nos(paths.paths_manager.paths_root_manifest_path).remove()
    assert _sql(paths).file_manifest("orders") == expected
    assert len(_sql(paths).files_ledger()) == 1
    assert len(_sql(paths).paths_ledger()) == 1


# ===================
# order
# ===================


def test_manifests_are_in_manifest_index_order_not_time(paths, tmp_path):
    _register(paths, tmp_path, n=0)
    _register(paths, tmp_path, n=1)
    _load(paths, tmp_path, n=0)
    _load(paths, tmp_path, n=1)
    expected_files = _fs(paths).file_manifest("orders")
    expected_paths = _fs(paths).paths_manifest("orders")
    #
    # reverse the times: order must not depend on them
    #
    for table in ["named_file", "named_paths"]:
        _execute(paths, f"update {table} set at = datetime('2000-01-01') where manifest_index = 1")
    assert _sql(paths).file_manifest("orders") == expected_files
    assert _sql(paths).paths_manifest("orders") == expected_paths


def test_ledgers_are_in_ledger_index_order_not_time(paths, tmp_path):
    _register(paths, tmp_path, n=0)
    _register(paths, tmp_path, n=1)
    expected = _fs(paths).files_ledger()
    _execute(
        paths,
        "update named_file_ledger set at = datetime('2000-01-01') where ledger_index = 1",
    )
    assert _sql(paths).files_ledger() == expected


def test_names_are_sorted_in_both_sources(paths, tmp_path):
    for name in ["b", "Z", "a"]:
        _register(paths, tmp_path, name=name)
        _load(paths, tmp_path, name=name)
    expected = ["Z", "a", "b"]
    assert _sql(paths).file_names() == _fs(paths).file_names() == expected
    assert _sql(paths).paths_names() == _fs(paths).paths_names() == expected


# ===================
# lifecycle
# ===================


def test_deleted_versions_and_names_are_skipped(paths, tmp_path):
    _register(paths, tmp_path, n=0)
    _register(paths, tmp_path, name="people")
    paths.file_manager.remove_named_file("orders")
    _register(paths, tmp_path, n=1)
    _load(paths, tmp_path, name="beta")
    paths.paths_manager.remove_named_paths("beta")
    sql, fs = _sql(paths), _fs(paths)
    assert sql.file_manifest("orders") == fs.file_manifest("orders")
    assert len(sql.file_manifest("orders")) == 1
    assert sql.paths_names() == fs.paths_names() == []
    assert sql.paths_manifest("beta") == []


def test_ledgers_keep_deleted_entries(paths, tmp_path):
    _register(paths, tmp_path)
    paths.file_manager.remove_named_file("orders")
    _load(paths, tmp_path)
    paths.paths_manager.remove_named_paths("orders")
    assert [e["lifecycle"] for e in _sql(paths).files_ledger()] == ["deleted"]
    assert [e["lifecycle"] for e in _sql(paths).paths_ledger()] == ["deleted"]
    assert _sql(paths).file_names() == []


def test_rows_with_no_lifecycle_are_not_seen(paths, tmp_path):
    #
    # rows from before lifecycles; on assumes SQL mirrored from the start
    #
    _register(paths, tmp_path)
    _load(paths, tmp_path)
    _execute(paths, "update named_file set lifecycle = NULL")
    _execute(paths, "update named_paths set lifecycle = NULL")
    assert _sql(paths).file_names() == []
    assert _sql(paths).paths_names() == []
    assert _sql(paths).paths_manifest("orders") == []
    with pytest.raises(ValueError):
        _sql(paths).file_manifest("orders")


# ===================
# missing names and scoping
# ===================


def test_a_missing_named_file_raises_as_the_filesystem_does(paths):
    with pytest.raises(ValueError, match="No manifest for file named nope"):
        _sql(paths).file_manifest("nope")
    with pytest.raises(ValueError, match="No manifest for file named nope"):
        _fs(paths).file_manifest("nope")


def test_a_missing_named_paths_is_empty_and_creates_nothing(paths):
    assert _sql(paths).paths_manifest("nope") == []
    assert not paths.paths_manager.has_named_paths("nope")


def test_reads_are_scoped_to_the_configured_roots(paths, tmp_path):
    _register(paths, tmp_path)
    _load(paths, tmp_path)
    other = _paths(tmp_path, root="b")
    _register(other, tmp_path, name="other")
    _load(other, tmp_path, name="other")
    assert _sql(paths).file_names() == ["orders"]
    assert _sql(paths).paths_names() == ["orders"]
    assert len(_sql(paths).files_ledger()) == 1
    assert len(_sql(paths).paths_ledger()) == 1
    assert _sql(other).file_names() == ["other"]
    with pytest.raises(ValueError):
        _sql(other).file_manifest("orders")
    rows = _sql(paths)._column(text("select count(*) from named_file"))
    assert rows == [2]


# ===================
# choosing the source
# ===================


def _mode(p: CsvPaths, mode: str) -> None:
    p.config.add_to_config(section="references", key="sql", value=mode)


@pytest.mark.parametrize("mode", ["off", "shadow"])
def test_off_and_shadow_read_the_filesystem(paths, mode):
    _mode(paths, mode)
    s = paths.reference_source
    assert type(s) is FilesystemReferenceSource


def test_on_reads_sql(paths):
    _mode(paths, "on")
    assert type(paths.reference_source) is SqlReferenceSource


def test_the_source_is_built_once_per_mode(paths):
    _mode(paths, "on")
    first = paths.reference_source
    assert paths.reference_source is first
    _mode(paths, "off")
    off = paths.reference_source
    assert type(off) is FilesystemReferenceSource
    assert paths.reference_source is off
    _mode(paths, "on")
    assert paths.reference_source is not first
    assert type(paths.reference_source) is SqlReferenceSource


def test_on_checks_the_configuration_once(paths, monkeypatch):
    calls = []
    real = ReferencesSqlCheck.check

    def check(*, csvpaths):
        calls.append(csvpaths)
        real(csvpaths=csvpaths)

    monkeypatch.setattr(ReferencesSqlCheck, "check", check)
    _mode(paths, "on")
    paths.reference_source
    paths.reference_source
    assert calls == [paths]


def test_on_with_a_configuration_that_cannot_work_raises(tmp_path):
    _clear_engine()
    p = _paths(tmp_path, groups="")
    _mode(p, "on")
    try:
        with pytest.raises(ConfigurationException):
            p.reference_source
        #
        # and so does the first reference
        #
        with pytest.raises(ConfigurationException):
            ReferenceFinderFactory3.for_reference(
                reference="$orders.files.:last()", csvpaths=p
            ).query()
    finally:
        _clear_engine()


def test_finders_read_from_the_csvpaths_source(paths, tmp_path):
    _register(paths, tmp_path)
    _mode(paths, "on")
    finder = ReferenceFinderFactory3.for_reference(
        reference="$orders.files.:last()", csvpaths=paths
    )
    assert finder.source is paths.reference_source
    assert len(finder.query()) == 1


def test_finders_over_stand_ins_read_the_filesystem(paths):
    class StandIn:
        def __init__(self, p):
            self.config = p.config
            self.file_manager = p.file_manager
            self.paths_manager = p.paths_manager
            self.results_manager = p.results_manager
            self.logger = p.logger

    finder = ReferenceFinderFactory3.for_reference(
        reference="$orders.files.:last()", csvpaths=StandIn(paths)
    )
    assert type(finder.source) is FilesystemReferenceSource


# ===================
# ReferencesSqlCheck
# ===================


def test_check_requires_the_lifecycle_column(paths):
    engine = _sql(paths).engine
    _sql(paths).tables.assure_tables()
    assert ReferencesSqlCheck._missing(engine=engine) == []
    with engine.connect() as conn:
        conn.execute(text("alter table named_file drop column lifecycle"))
        conn.commit()
    problems = ReferencesSqlCheck._missing(engine=engine)
    assert problems == ["table named_file has no lifecycle column"]


# ===================
# RESULTS
# ===================

GROUP = """~ id: first ~ $[*][yes()]

---- CSVPATH ----

~ id: second ~ $[*][no()]

---- CSVPATH ----

$[*][yes()]"""


def _run(p: CsvPaths, tmp_path, *, name: str = "orders") -> None:
    data = tmp_path / f"{name}_run.csv"
    data.write_text("id,amount\n1,10\n2,20\n", encoding="utf-8")
    if not p.file_manager.has_named_file(name):
        p.file_manager.add_named_file(name=name, path=str(data))
    group = tmp_path / f"{name}_run.csvpaths"
    group.write_text(GROUP, encoding="utf-8")
    if not p.paths_manager.has_named_paths(name):
        p.paths_manager.add_named_paths_from_file(name=name, file_path=str(group))
    p.collect_paths(pathsname=name, filename=name)


def _homes(source, name: str = "orders") -> list[str]:
    return [h for h, _ in source.run_homes(root_major=name, name_filter=None)]


def test_results_reads_equal_the_filesystem(paths, tmp_path):
    _run(paths, tmp_path)
    _run(paths, tmp_path)
    _run(paths, tmp_path, name="beta")
    sql, fs = _sql(paths), _fs(paths)
    assert sql.results_ledger() == fs.results_ledger()
    assert len(sql.results_ledger()) == 9
    for args in [
        {"root_major": None, "name_filter": None},
        {"root_major": "orders", "name_filter": None},
        {"root_major": None, "name_filter": "^b"},
    ]:
        assert sql.run_homes(**args) == fs.run_homes(**args)
    homes = [h for h, _ in sql.run_homes(root_major=None, name_filter=None)]
    assert len(homes) == 3
    for home in homes:
        assert sql.run_manifest(home) == fs.run_manifest(home)
        assert sorted(sql.instance_dirs(home)) == sorted(fs.instance_dirs(home))
        assert len(sql.instance_dirs(home)) == 3
        for d in fs.instance_dirs(home):
            inst = Nos(home).join(d)
            assert sql.instance_manifest(inst) == fs.instance_manifest(inst)


def test_results_reads_come_from_sql(paths, tmp_path):
    _run(paths, tmp_path)
    sql = _sql(paths)
    home = _homes(sql)[0]
    run = sql.run_manifest(home)
    dirs = sorted(sql.instance_dirs(home))
    inst = Nos(home).join(dirs[0])
    instance = sql.instance_manifest(inst)
    #
    # remove the JSON; keep the run directory, which run_homes checks
    #
    Nos(Nos(home).join("manifest.json")).remove()
    Nos(Nos(inst).join("manifest.json")).remove()
    Nos(paths.results_manager.results_root_manifest_path).remove()
    for d in dirs:
        shutil.rmtree(Nos(home).join(d))
    assert len(sql.results_ledger()) == 3
    assert _homes(sql) == [home]
    assert sql.run_manifest(home) == run
    assert sql.instance_manifest(inst) == instance
    assert sorted(sql.instance_dirs(home)) == dirs


def test_a_deleted_run_is_dropped_by_the_existence_check(paths, tmp_path):
    _run(paths, tmp_path)
    _run(paths, tmp_path)
    sql, fs = _sql(paths), _fs(paths)
    first = _homes(sql)[0]
    shutil.rmtree(first)
    assert _homes(sql) == _homes(fs)
    assert first not in _homes(sql)
    assert len(_homes(sql)) == 1
    #
    # the ledger keeps the run's entries
    #
    assert len(sql.results_ledger()) == 6


def test_unknown_runs_and_instances_are_none(paths, tmp_path):
    _run(paths, tmp_path)
    sql = _sql(paths)
    home = _homes(sql)[0]
    assert sql.run_manifest(home + "_nope") is None
    assert sql.instance_manifest(Nos(home).join("nope")) is None
    assert sql.instance_dirs(home + "_nope") == []
    assert _homes(sql, "nope") == []


def test_results_reads_are_scoped_by_archive_root(paths, tmp_path):
    _run(paths, tmp_path)
    other = _paths(tmp_path, root="b")
    _run(other, tmp_path / "a")
    mine, theirs = _sql(paths), _sql(other)
    assert len(mine.results_ledger()) == 3
    assert len(theirs.results_ledger()) == 3
    their_home = _homes(theirs)[0]
    assert mine.run_manifest(their_home) is None
    assert mine.instance_dirs(their_home) == []
    d = theirs.instance_dirs(their_home)[0]
    assert mine.instance_manifest(Nos(their_home).join(d)) is None
    assert theirs.instance_manifest(Nos(their_home).join(d)) is not None


def test_duplicate_rows_raise(paths, tmp_path):
    _run(paths, tmp_path)
    sql = _sql(paths)
    home = _homes(sql)[0]
    _execute(
        paths,
        "insert into named_paths_group_run "
        "select 'dup' as uuid, at, time_completed, status, by_line_run, "
        "all_completed, all_valid, error_count, all_expected_files, "
        "archive_name, archive_root, run_home, named_results_name, "
        "named_paths_uuid, named_paths_name, named_paths_home, "
        "named_file_uuid, named_file_name, named_file_home, named_file_path, "
        "named_file_size, named_file_last_change, named_file_fingerprint, "
        "hostname, username, ip_address, manifest_path, manifest_entry, lifecycle "
        "from named_paths_group_run",
    )
    with pytest.raises(ValueError, match="2 SQL rows for run"):
        sql.run_manifest(home)


def test_run_homes_from_checks_its_entries():
    with pytest.raises(TypeError):
        FilesystemReferenceSource._run_homes_from(
            entries=None, root_major=None, name_filter=None
        )
