"""ReferencesSqlCoverage reports whether SQL holds everything the JSON root
ledgers hold (step 6, PR 1).

The first half uses stub sources and ReferencesSqlCheck.problems() patched
to report nothing, so each finding is set up exactly. The second half uses
real sources over SQLite in pytest's tmp_path: SQL on from the start, SQL
switched on late, a lost SQL write, and a config without SQL.
"""

import pytest
from sqlalchemy import text

from csvpath import CsvPaths
from csvpath.managers.integrations.sql.references_sql_check import (
    ReferencesSqlCheck,
)
from csvpath.references.sources.filesystem_reference_source import (
    FilesystemReferenceSource,
)
from csvpath.references.sources.reference_source import ReferenceSource
from csvpath.references.sources.references_sql_coverage import (
    ReferencesSqlCoverage,
)
from csvpath.references.sources.sql_reference_source import SqlReferenceSource
from csvpath.util.box import Box


def _e(n: int, *, name: str = "orders", **kw) -> dict:
    e = {"uuid": f"u{n}", "time": f"2026-07-{n:02d}", "named_file_name": name}
    e["named_paths_name"] = name
    e.update(kw)
    return e


class _Stub(ReferenceSource):
    """returns the ledgers it is given; anything else is not called"""

    def __init__(
        self, *, csvpaths, files=None, paths=None, results=None, raises=None
    ):
        super().__init__(csvpaths=csvpaths)
        self.ledgers = {
            "files_ledger": files,
            "paths_ledger": paths,
            "results_ledger": results,
        }
        self.raises = raises
        self.calls = []

    def _read(self, method):
        self.calls.append(method)
        if self.raises is not None:
            raise self.raises
        return self.ledgers[method]

    def files_ledger(self):
        return self._read("files_ledger")

    def paths_ledger(self):
        return self._read("paths_ledger")

    def results_ledger(self):
        return self._read("results_ledger")

    def file_manifest(self, name):
        raise AssertionError("not a ledger read")

    def file_names(self):
        raise AssertionError("not a ledger read")

    def paths_manifest(self, name):
        raise AssertionError("not a ledger read")

    def paths_names(self):
        raise AssertionError("not a ledger read")

    def run_homes(self, *, root_major, name_filter):
        raise AssertionError("not a ledger read")

    def run_manifest(self, run_dir):
        raise AssertionError("not a ledger read")

    def instance_manifest(self, instance_dir):
        raise AssertionError("not a ledger read")

    def instance_dirs(self, run_dir):
        raise AssertionError("not a ledger read")


@pytest.fixture
def csvpaths():
    return CsvPaths()


@pytest.fixture
def no_problems(monkeypatch):
    monkeypatch.setattr(ReferencesSqlCheck, "problems", classmethod(lambda c, **k: []))


def _coverage(csvpaths, *, json: dict, sql: dict, raises=None):
    return ReferencesSqlCoverage(
        csvpaths=csvpaths,
        primary=_Stub(csvpaths=csvpaths, **json),
        secondary=_Stub(csvpaths=csvpaths, raises=raises, **sql),
    )


def _cmp(json, sql, name_key="named_file_name"):
    return ReferencesSqlCoverage.compare(
        json_ledger=json, sql_ledger=sql, name_key=name_key
    )


ALL = [_e(1), _e(2), _e(3), _e(4)]


# ===================
# construction
# ===================


def test_csvpaths_cannot_be_none():
    with pytest.raises(ValueError):
        ReferencesSqlCoverage(csvpaths=None)


@pytest.mark.parametrize("which", ["primary", "secondary"])
@pytest.mark.parametrize("bad", ["fs", 1, object()])
def test_sources_must_be_reference_sources(csvpaths, which, bad):
    with pytest.raises(TypeError):
        ReferencesSqlCoverage(csvpaths=csvpaths, **{which: bad})


def test_the_default_primary_is_the_filesystem(csvpaths):
    c = ReferencesSqlCoverage(csvpaths=csvpaths)
    assert type(c.primary) is FilesystemReferenceSource


def test_the_ledgers_compared():
    assert ReferencesSqlCoverage.LEDGERS == {
        "files": ("files_ledger", "named_file_name"),
        "csvpaths": ("paths_ledger", "named_paths_name"),
        "results": ("results_ledger", "named_paths_name"),
    }


# ===================
# compare: one ledger
# ===================


def test_the_same_ledger_is_covered():
    r = _cmp(ALL, list(ALL))
    assert r == {
        "json": 4,
        "sql": 4,
        "both": 4,
        "missing": 0,
        "missing_before_sql": 0,
        "missing_after_sql": 0,
        "missing_by_name": {},
        "missing_first_time": None,
        "missing_last_time": None,
        "sql_first_time": "2026-07-01",
        "only_in_sql": 0,
        "differ": 0,
        "no_uuid": 0,
        "duplicate_uuids": 0,
        "order_differs": False,
    }
    assert ReferencesSqlCoverage.ledger_covered(ledger=r)


def test_empty_and_missing_ledgers_are_covered():
    for json, sql in [([], []), (None, []), (None, None), ([], None)]:
        r = _cmp(json, sql)
        assert r["json"] == 0 and r["sql"] == 0
        assert ReferencesSqlCoverage.ledger_covered(ledger=r)


def test_sql_switched_on_late():
    r = _cmp(ALL, ALL[2:])
    assert r["missing"] == 2
    assert r["missing_before_sql"] == 2
    assert r["missing_after_sql"] == 0
    assert r["missing_first_time"] == "2026-07-01"
    assert r["missing_last_time"] == "2026-07-02"
    assert r["sql_first_time"] == "2026-07-03"
    assert not ReferencesSqlCoverage.ledger_covered(ledger=r)


def test_sql_with_none_of_the_ledger():
    r = _cmp(ALL, [])
    assert r["missing"] == 4
    assert r["missing_before_sql"] == 4
    assert r["missing_after_sql"] == 0
    assert r["sql_first_time"] is None


def test_a_gap_after_sql_began():
    r = _cmp(ALL, [ALL[0], ALL[1], ALL[3]])
    assert r["missing"] == 1
    assert r["missing_before_sql"] == 0
    assert r["missing_after_sql"] == 1
    assert r["missing_first_time"] == "2026-07-03"
    assert r["sql_first_time"] == "2026-07-01"


def test_a_late_start_and_a_gap():
    r = _cmp(ALL, [ALL[1], ALL[3]])
    assert (r["missing_before_sql"], r["missing_after_sql"]) == (1, 1)


def test_missing_by_name():
    json = [_e(1, name="a"), _e(2, name="b"), _e(3, name="a"), _e(4, name="c")]
    r = _cmp(json, [json[3]])
    assert r["missing_by_name"] == {"a": 2, "b": 1}


def test_missing_by_name_uses_the_name_key():
    json = [{"uuid": "u1", "named_paths_name": "g", "named_file_name": "f"}]
    assert _cmp(json, [], "named_paths_name")["missing_by_name"] == {"g": 1}
    assert _cmp(json, [], "named_file_name")["missing_by_name"] == {"f": 1}


def test_an_entry_only_in_sql():
    r = _cmp(ALL[:3], ALL)
    assert r["only_in_sql"] == 1
    assert r["missing"] == 0
    assert not ReferencesSqlCoverage.ledger_covered(ledger=r)


def test_a_changed_entry_differs():
    sql = [dict(e) for e in ALL]
    sql[2]["lifecycle"] = "deleted"
    r = _cmp(ALL, sql)
    assert r["differ"] == 1
    assert r["both"] == 4
    assert r["missing"] == 0
    assert not ReferencesSqlCoverage.ledger_covered(ledger=r)


def test_a_different_order():
    r = _cmp(ALL, [ALL[1], ALL[0], ALL[2], ALL[3]])
    assert r["order_differs"]
    assert r["differ"] == 0 and r["missing"] == 0
    assert not ReferencesSqlCoverage.ledger_covered(ledger=r)


def test_order_is_compared_over_the_shared_entries_only():
    #
    # a late start is not also an order difference
    #
    r = _cmp(ALL, ALL[2:])
    assert not r["order_differs"]


def test_entries_without_a_uuid():
    json = [_e(1), {"time": "x"}, "not a dict", _e(2)]
    r = _cmp(json, [_e(1), _e(2)])
    assert r["no_uuid"] == 2
    assert r["missing"] == 0
    assert not ReferencesSqlCoverage.ledger_covered(ledger=r)


def test_a_repeated_uuid():
    r = _cmp(ALL + [_e(2)], ALL)
    assert r["duplicate_uuids"] == 1
    assert r["both"] == 4
    assert not ReferencesSqlCoverage.ledger_covered(ledger=r)


@pytest.mark.parametrize("gap", ReferencesSqlCoverage.GAPS)
def test_every_gap_count_stops_coverage(gap):
    r = _cmp(ALL, ALL)
    assert ReferencesSqlCoverage.ledger_covered(ledger=r)
    r[gap] = 1
    assert not ReferencesSqlCoverage.ledger_covered(ledger=r)


@pytest.mark.parametrize(
    "json,sql,key,error",
    [
        ("x", [], "k", TypeError),
        ({}, [], "k", TypeError),
        ([], "x", "k", TypeError),
        ([], [], None, ValueError),
        ([], [], "", ValueError),
        ([], [], 1, ValueError),
    ],
)
def test_compare_checks_its_arguments(json, sql, key, error):
    with pytest.raises(error):
        _cmp(json, sql, key)


@pytest.mark.parametrize("bad", [None, [], "x"])
def test_ledger_covered_checks_its_argument(bad):
    with pytest.raises(TypeError):
        ReferencesSqlCoverage.ledger_covered(ledger=bad)


# ===================
# report: stub sources
# ===================


def test_a_covered_report(csvpaths, no_problems):
    c = _coverage(
        csvpaths,
        json={"files": ALL, "paths": ALL[:2], "results": []},
        sql={"files": ALL, "paths": ALL[:2], "results": []},
    )
    r = c.report()
    assert r["problems"] == []
    assert r["covered"] is True
    assert sorted(r["ledgers"]) == ["csvpaths", "files", "results"]
    assert r["ledgers"]["files"]["both"] == 4
    assert r["ledgers"]["csvpaths"]["both"] == 2
    assert r["config"] == csvpaths.config.config_path
    assert r["mode"] == csvpaths.config.references_sql


def test_each_ledger_goes_to_its_own_datatype(csvpaths, no_problems):
    c = _coverage(
        csvpaths,
        json={"files": ALL, "paths": ALL[:3], "results": ALL[:2]},
        sql={"files": [], "paths": [], "results": []},
    )
    ledgers = c.report()["ledgers"]
    assert ledgers["files"]["missing"] == 4
    assert ledgers["csvpaths"]["missing"] == 3
    assert ledgers["results"]["missing"] == 2


@pytest.mark.parametrize(
    "datatype,arg",
    [("files", "files"), ("csvpaths", "paths"), ("results", "results")],
)
def test_one_uncovered_ledger_uncovers_the_report(
    csvpaths, no_problems, datatype, arg
):
    json = {"files": ALL, "paths": ALL, "results": ALL}
    sql = dict(json)
    sql[arg] = ALL[1:]
    r = _coverage(csvpaths, json=json, sql=sql).report()
    assert r["covered"] is False
    assert [d for d, l in r["ledgers"].items() if l["missing"]] == [datatype]


def test_problems_stop_the_sql_reads(csvpaths, monkeypatch):
    monkeypatch.setattr(
        ReferencesSqlCheck, "problems", classmethod(lambda c, **k: ["no dialect"])
    )
    c = _coverage(csvpaths, json={"files": ALL}, sql={"files": ALL})
    r = c.report()
    assert r["problems"] == ["no dialect"]
    assert r["ledgers"] == {}
    assert r["covered"] is False
    assert c.primary.calls == []
    assert c.secondary.calls == []


def test_problems_are_checked_for_this_csvpaths(csvpaths, monkeypatch):
    seen = []

    def problems(cls, *, csvpaths):
        seen.append(csvpaths)
        return []

    monkeypatch.setattr(ReferencesSqlCheck, "problems", classmethod(problems))
    _coverage(csvpaths, json={}, sql={}).report()
    assert seen == [csvpaths]


class _Logger:
    def __init__(self):
        self.errors = []
        self.exceptions = []

    def error(self, msg):
        self.errors.append(msg)

    def exception(self, ex):
        self.exceptions.append(ex)


def test_a_sql_read_that_raises_is_logged_and_raised(
    csvpaths, no_problems, monkeypatch
):
    log = _Logger()
    monkeypatch.setattr(type(csvpaths), "logger", property(lambda s: log))
    boom = RuntimeError("boom")
    c = _coverage(csvpaths, json={"files": ALL}, sql={}, raises=boom)
    with pytest.raises(RuntimeError, match="boom"):
        c.report()
    assert log.errors == ["SQL coverage: SQL files_ledger() raised: boom"]
    assert log.exceptions == [boom]


def test_the_sql_source_is_not_built_when_there_are_problems(tmp_path, monkeypatch):
    built = []
    import csvpath.references.sources.sql_reference_source as srs

    monkeypatch.setattr(
        srs.SqlReferenceSource, "__init__", lambda s, **k: built.append(1)
    )
    p = _paths(tmp_path, groups="")
    try:
        r = ReferencesSqlCoverage(csvpaths=p).report()
        assert r["problems"] != []
        assert built == []
    finally:
        _clear_engine()


# ===================
# format
# ===================


def _report(csvpaths, *, json, sql):
    return ReferencesSqlCoverage(
        csvpaths=csvpaths,
        primary=_Stub(csvpaths=csvpaths, **json),
        secondary=_Stub(csvpaths=csvpaths, **sql),
    ).report()


def test_format_a_covered_report(csvpaths, no_problems):
    r = _report(csvpaths, json={"files": ALL}, sql={"files": ALL})
    s = ReferencesSqlCoverage.format(report=r)
    assert "references SQL coverage" in s
    assert f"config: {csvpaths.config.config_path}" in s
    assert "COVERED: [references] sql = on will see everything" in s
    assert "NOT COVERED" not in s
    assert "missing from SQL" not in s


def test_format_a_late_start(csvpaths, no_problems):
    json = [_e(1, name="a"), _e(2, name="b"), _e(3, name="a"), _e(4)]
    r = _report(csvpaths, json={"files": json}, sql={"files": json[3:]})
    s = ReferencesSqlCoverage.format(report=r)
    assert (
        "files: 3 entries missing from SQL, all before SQL's first entry "
        "(2026-07-04): SQL was switched on after they were written"
    ) in s
    assert "2026-07-01 .. 2026-07-03; by name: a 2, b 1" in s
    assert "NOT COVERED" in s
    assert "(3 entries missing from SQL)" in s


def test_format_sql_with_none_of_a_ledger(csvpaths, no_problems):
    r = _report(csvpaths, json={"paths": ALL}, sql={"paths": []})
    s = ReferencesSqlCoverage.format(report=r)
    assert "csvpaths: 4 entries missing from SQL, SQL has none of this ledger" in s


def test_format_a_gap(csvpaths, no_problems):
    r = _report(csvpaths, json={"results": ALL}, sql={"results": [ALL[0], ALL[3]]})
    s = ReferencesSqlCoverage.format(report=r)
    assert (
        "results: 2 entries missing from SQL AFTER its first entry "
        "(2026-07-01): SQL writes failed while SQL was on"
    ) in s


def test_format_the_other_findings(csvpaths, no_problems):
    sql = [dict(e) for e in [ALL[1], ALL[0], ALL[2], ALL[3], _e(9)]]
    sql[0]["status"] = "x"
    json = ALL + [_e(1), {"time": "t"}]
    r = _report(csvpaths, json={"files": json}, sql={"files": sql})
    s = ReferencesSqlCoverage.format(report=r)
    assert "files: 1 entries are in SQL but not the JSON ledger" in s
    assert "files: 1 entries differ between the JSON ledger and SQL" in s
    assert "files: SQL holds the entries in a different order" in s
    assert "files: 1 JSON entries have no uuid and cannot be matched" in s
    assert "files: 1 JSON entries repeat a uuid" in s
    assert "NOT COVERED" in s


def test_format_the_table(csvpaths, no_problems):
    r = _report(csvpaths, json={"files": ALL}, sql={"files": ALL[1:]})
    lines = ReferencesSqlCoverage.format(report=r).splitlines()
    header = [l for l in lines if "only_in_sql" in l]
    assert len(header) == 1
    assert header[0].split() == [
        "json", "sql", "both", "missing", "only_in_sql", "differ"
    ]
    files = [l for l in lines if l.startswith("files ")]
    assert files[0].split() == ["files", "4", "3", "3", "1", "0", "0"]


def test_format_problems(csvpaths, monkeypatch):
    monkeypatch.setattr(
        ReferencesSqlCheck, "problems", classmethod(lambda c, **k: ["p1", "p2"])
    )
    r = ReferencesSqlCoverage(csvpaths=csvpaths).report()
    s = ReferencesSqlCoverage.format(report=r)
    assert "SQL cannot be used, so it was not read:" in s
    assert "  - p1" in s and "  - p2" in s
    assert "NOT READY" in s
    assert "COVERED" not in s


@pytest.mark.parametrize("bad", [None, [], "x"])
def test_format_checks_its_argument(bad):
    with pytest.raises(TypeError):
        ReferencesSqlCoverage.format(report=bad)


# ===================
# report: real sources
# ===================


def _clear_engine() -> None:
    box = Box()
    e = box.get(key=Box.SQL_ENGINE)
    if e is not None:
        e.dispose()
        box.remove(Box.SQL_ENGINE)


def _paths(tmp_path, *, groups: str = "sql") -> CsvPaths:
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
        value=f"sqlite:///{tmp_path / 'coverage.db'}",
    )
    return p


@pytest.fixture
def real(tmp_path):
    _clear_engine()
    yield tmp_path
    _clear_engine()


def _register(p: CsvPaths, tmp_path, *, name: str = "orders", n: int = 0) -> None:
    data = tmp_path / f"{name}_{n}.csv"
    data.write_text(f"id,amount\n{n},10\n", encoding="utf-8")
    p.file_manager.add_named_file(name=name, path=str(data))


def _load(p: CsvPaths, tmp_path, *, name: str = "orders", n: int = 0) -> None:
    f = tmp_path / f"{name}.csvpaths"
    f.write_text(f"~ id: s{n} ~ $[*][yes()]", encoding="utf-8")
    p.paths_manager.add_named_paths_from_file(name=name, file_path=str(f))


def _activity(p: CsvPaths, tmp_path, *, start: int) -> None:
    """two file versions, one paths version and one run, numbered from start"""
    _register(p, tmp_path, n=start)
    _register(p, tmp_path, n=start + 1)
    _load(p, tmp_path, n=start)
    p.collect_paths(pathsname="orders", filename="orders")


def test_sql_on_from_the_start_is_covered(real):
    p = _paths(real)
    _activity(p, real, start=0)
    _activity(p, real, start=10)
    r = ReferencesSqlCoverage(csvpaths=p).report()
    assert r["problems"] == []
    assert r["covered"] is True, ReferencesSqlCoverage.format(report=r)
    for ledger in r["ledgers"].values():
        assert ledger["json"] > 0
        assert ledger["json"] == ledger["sql"] == ledger["both"]


def test_sql_switched_on_late_is_reported_as_missing_before_sql(real):
    p = _paths(real, groups="")
    _activity(p, real, start=0)
    fs = FilesystemReferenceSource(csvpaths=p)
    before = {
        "files": len(fs.files_ledger()),
        "csvpaths": len(fs.paths_ledger()),
        "results": len(fs.results_ledger()),
    }
    p.config.add_to_config(section="listeners", key="groups", value="sql")
    _activity(p, real, start=10)
    r = ReferencesSqlCoverage(csvpaths=p).report()
    assert r["problems"] == []
    assert r["covered"] is False
    for datatype, n in before.items():
        ledger = r["ledgers"][datatype]
        assert n > 0, datatype
        assert ledger["missing"] == n, datatype
        assert ledger["missing_before_sql"] == n, datatype
        assert ledger["missing_after_sql"] == 0, datatype
        assert ledger["both"] == ledger["sql"] == ledger["json"] - n, datatype
        assert ledger["only_in_sql"] == 0, datatype
        assert ledger["differ"] == 0, datatype
        assert ledger["missing_by_name"] == {"orders": n}, datatype
    s = ReferencesSqlCoverage.format(report=r)
    assert "SQL was switched on after they were written" in s


def test_a_lost_sql_write_is_reported_as_a_gap(real):
    p = _paths(real)
    _register(p, real, n=0)
    _register(p, real, n=1)
    _register(p, real, n=2)
    middle = FilesystemReferenceSource(csvpaths=p).files_ledger()[1]["uuid"]
    with SqlReferenceSource(csvpaths=p).engine.connect() as conn:
        conn.execute(
            text("delete from named_file_ledger where uuid = :u"), {"u": middle}
        )
        conn.commit()
    r = ReferencesSqlCoverage(csvpaths=p).report()
    files = r["ledgers"]["files"]
    assert files["missing"] == 1
    assert files["missing_after_sql"] == 1
    assert files["missing_before_sql"] == 0
    assert r["covered"] is False
    assert "SQL writes failed while SQL was on" in ReferencesSqlCoverage.format(
        report=r
    )


def test_a_changed_sql_row_differs(real):
    p = _paths(real)
    _register(p, real, n=0)
    with SqlReferenceSource(csvpaths=p).engine.connect() as conn:
        conn.execute(
            text("update named_file_ledger set ledger_entry = :e"),
            {"e": '{"uuid": "x"}'},
        )
        conn.commit()
    r = ReferencesSqlCoverage(csvpaths=p).report()
    files = r["ledgers"]["files"]
    #
    # the changed row now has another uuid: one missing, one only in SQL
    #
    assert files["missing"] == 1 and files["only_in_sql"] == 1
    assert r["covered"] is False


def test_a_config_without_sql_reports_its_problems(real):
    p = _paths(real, groups="")
    p.config.add_to_config(section="sql", key="dialect", value="")
    r = ReferencesSqlCoverage(csvpaths=p).report()
    assert "[sql] dialect is not set" in r["problems"]
    assert any("SqlFileListener" in x for x in r["problems"])
    assert r["covered"] is False
    assert r["ledgers"] == {}


def test_the_report_does_not_depend_on_the_references_mode(real):
    p = _paths(real)
    _register(p, real)
    reports = []
    for mode in ["off", "on", "shadow"]:
        p.config.add_to_config(section="references", key="sql", value=mode)
        r = ReferencesSqlCoverage(csvpaths=p).report()
        assert r["mode"] == mode
        reports.append({k: v for k, v in r.items() if k != "mode"})
    p.config.add_to_config(section="references", key="sql", value="off")
    assert reports[0] == reports[1] == reports[2]
