"""ShadowReferenceSource, used when [references] sql = shadow (step 5): every
read goes to a primary (the filesystem) and a secondary (SQL), the two are
compared, differences are logged as warnings, and the primary's result is
returned. A secondary that raises is logged and raised.

These tests use stub sources and a stub CsvPaths, so no files or database
are involved. Shadow over real sources is tested in
test_sql_reference_source.py and test_sql_reference_parity.py.
"""

import pytest

from csvpath.references.sources.reference_source import ReferenceSource
from csvpath.references.sources.shadow_reference_source import (
    ShadowReferenceSource,
)

#
# method -> (args, kwargs) used to call it
#
CALLS = {
    "file_manifest": (("orders",), {}),
    "files_ledger": ((), {}),
    "file_names": ((), {}),
    "paths_manifest": (("acme",), {}),
    "paths_ledger": ((), {}),
    "paths_names": ((), {}),
    "results_ledger": ((), {}),
    "run_homes": ((), {"root_major": "acme", "name_filter": None}),
    "run_manifest": (("/ar/acme/run",), {}),
    "instance_manifest": (("/ar/acme/run/one",), {}),
    "instance_dirs": (("/ar/acme/run",), {}),
}


class Logger:
    def __init__(self):
        self.warnings = []
        self.errors = []
        self.exceptions = []

    def warning(self, msg):
        self.warnings.append(msg)

    def error(self, msg):
        self.errors.append(msg)

    def exception(self, ex):
        self.exceptions.append(ex)


class Paths:
    def __init__(self):
        self.logger = Logger()


class Stub(ReferenceSource):
    """returns values[method] for every read, or raises it if it is an
    exception, and records every call"""

    def __init__(self, *, csvpaths, values: dict):
        super().__init__(csvpaths=csvpaths)
        self.values = values
        self.calls = []

    def _read(self, method, *args, **kwargs):
        self.calls.append((method, args, kwargs))
        v = self.values.get(method)
        if isinstance(v, Exception):
            raise v
        return v

    def file_manifest(self, name):
        return self._read("file_manifest", name)

    def files_ledger(self):
        return self._read("files_ledger")

    def file_names(self):
        return self._read("file_names")

    def paths_manifest(self, name):
        return self._read("paths_manifest", name)

    def paths_ledger(self):
        return self._read("paths_ledger")

    def paths_names(self):
        return self._read("paths_names")

    def results_ledger(self):
        return self._read("results_ledger")

    def run_homes(self, *, root_major, name_filter):
        return self._read("run_homes", root_major=root_major, name_filter=name_filter)

    def run_manifest(self, run_dir):
        return self._read("run_manifest", run_dir)

    def instance_manifest(self, instance_dir):
        return self._read("instance_manifest", instance_dir)

    def instance_dirs(self, run_dir):
        return self._read("instance_dirs", run_dir)


def _shadow(*, fs: dict, sql: dict):
    p = Paths()
    primary = Stub(csvpaths=p, values=fs)
    secondary = Stub(csvpaths=p, values=sql)
    shadow = ShadowReferenceSource(csvpaths=p, primary=primary, secondary=secondary)
    p.logger.warnings.clear()
    return shadow, p.logger


def _call(shadow, method):
    args, kwargs = CALLS[method]
    return getattr(shadow, method)(*args, **kwargs)


# ===================
# construction
# ===================


def test_is_a_reference_source():
    s, _ = _shadow(fs={}, sql={})
    assert isinstance(s, ReferenceSource)


def test_csvpaths_cannot_be_none():
    with pytest.raises(ValueError):
        ShadowReferenceSource(csvpaths=None)


@pytest.mark.parametrize("which", ["primary", "secondary"])
@pytest.mark.parametrize("bad", ["fs", 1, object()])
def test_sources_must_be_reference_sources(which, bad):
    p = Paths()
    kwargs = {
        "primary": Stub(csvpaths=p, values={}),
        "secondary": Stub(csvpaths=p, values={}),
    }
    kwargs[which] = bad
    with pytest.raises(TypeError):
        ShadowReferenceSource(csvpaths=p, **kwargs)


def test_building_one_warns_that_shadow_is_on():
    p = Paths()
    s = Stub(csvpaths=p, values={})
    ShadowReferenceSource(csvpaths=p, primary=s, secondary=s)
    assert len(p.logger.warnings) == 1
    assert "shadow" in p.logger.warnings[0]
    assert "not production" in p.logger.warnings[0]


def test_every_read_method_is_compared():
    #
    # all 11 ReferenceSource reads are overridden, none inherited
    #
    abstract = sorted(ReferenceSource.__abstractmethods__)
    assert abstract == sorted(CALLS)
    for method in abstract:
        assert method in ShadowReferenceSource.__dict__, method


def test_compare_checks_its_method():
    s, _ = _shadow(fs={}, sql={})
    for bad in [None, "", " ", 1]:
        with pytest.raises(ValueError):
            s._compare(method=bad, args=(), kwargs={})


# ===================
# matches
# ===================


@pytest.mark.parametrize("method", list(CALLS))
def test_a_match_returns_the_primary_and_counts(method):
    value = [{"uuid": "u1"}] if method != "run_manifest" else {"uuid": "u1"}
    s, log = _shadow(fs={method: value}, sql={method: value})
    assert _call(s, method) is s.primary.values[method]
    assert log.warnings == []
    assert s.counts == {
        method: {"reads": 1, "matches": 1, "differences": 0, "sql_errors": 0}
    }


@pytest.mark.parametrize("method", list(CALLS))
def test_both_sources_get_the_same_arguments(method):
    s, _ = _shadow(fs={}, sql={})
    _call(s, method)
    args, kwargs = CALLS[method]
    assert s.primary.calls == [(method, args, kwargs)]
    assert s.secondary.calls == [(method, args, kwargs)]


def test_counts_accumulate_per_method():
    s, _ = _shadow(fs={"file_names": ["a"]}, sql={"file_names": ["b"]})
    s.file_names()
    s.file_names()
    s.paths_names()
    assert s.counts["file_names"] == {
        "reads": 2,
        "matches": 0,
        "differences": 2,
        "sql_errors": 0,
    }
    assert s.counts["paths_names"]["matches"] == 1
    assert "run_homes" not in s.counts


def test_counts_is_a_copy():
    s, _ = _shadow(fs={}, sql={})
    s.file_names()
    s.counts["file_names"]["reads"] = 99
    s.counts.clear()
    assert s.counts["file_names"]["reads"] == 1


# ===================
# differences
# ===================


@pytest.mark.parametrize("method", list(CALLS))
def test_a_difference_returns_the_primary_and_warns_once(method):
    s, log = _shadow(fs={method: ["a"]}, sql={method: ["b"]})
    assert _call(s, method) == ["a"]
    assert len(log.warnings) == 1
    assert log.warnings[0].startswith(f"shadow: {method}(")
    assert "differs" in log.warnings[0]
    assert s.counts[method]["differences"] == 1
    assert s.counts[method]["matches"] == 0


def test_the_warning_names_the_arguments():
    s, log = _shadow(fs={"run_homes": [1]}, sql={"run_homes": []})
    s.run_homes(root_major="acme", name_filter="^a")
    assert "run_homes(root_major='acme', name_filter='^a')" in log.warnings[0]
    s, log = _shadow(fs={"file_manifest": [1]}, sql={"file_manifest": []})
    s.file_manifest("orders")
    assert "file_manifest('orders')" in log.warnings[0]


def test_a_missing_entry_is_described_by_index_and_uuid():
    fs = [{"uuid": "u0"}, {"uuid": "u1"}, {"uuid": "u2"}]
    s, log = _shadow(fs={"file_manifest": fs}, sql={"file_manifest": fs[:2]})
    s.file_manifest("orders")
    w = log.warnings[0]
    assert "lengths 3 vs 2" in w
    assert "first difference at index 2 (sql: missing)" in w
    assert "uuid u2" in w


def test_an_extra_sql_entry_is_described():
    fs = [{"uuid": "u0"}]
    sql = fs + [{"uuid": "u9"}]
    s, log = _shadow(fs={"paths_ledger": fs}, sql={"paths_ledger": sql})
    s.paths_ledger()
    assert "index 1 (filesystem: missing), uuid u9" in log.warnings[0]


def test_a_changed_entry_is_described():
    fs = [{"uuid": "u0"}, {"uuid": "u1", "status": "complete"}]
    sql = [{"uuid": "u0"}, {"uuid": "u1", "status": "failed"}]
    s, log = _shadow(fs={"files_ledger": fs}, sql={"files_ledger": sql})
    s.files_ledger()
    assert "lengths 2 vs 2; first difference at index 1, uuid u1" in log.warnings[0]


def test_a_dict_difference_names_the_keys():
    fs = {"uuid": "r1", "status": "complete", "time": "t", "only_fs": 1}
    sql = {"uuid": "r1", "status": "failed", "time": "t", "only_sql": None}
    s, log = _shadow(fs={"run_manifest": fs}, sql={"run_manifest": sql})
    assert s.run_manifest("/ar/acme/run") is fs
    assert "keys differ: ['only_fs', 'only_sql', 'status'], uuid r1" in log.warnings[0]


def test_the_warning_does_not_hold_the_values():
    fs = [{"uuid": "u0", "detail": "x" * 500}]
    s, log = _shadow(fs={"file_manifest": fs}, sql={"file_manifest": []})
    s.file_manifest("orders")
    assert "x" * 50 not in log.warnings[0]


def test_none_and_an_empty_list_differ():
    s, log = _shadow(fs={"files_ledger": None}, sql={"files_ledger": []})
    assert s.files_ledger() is None
    assert "filesystem NoneType, sql list" in log.warnings[0]


def test_order_matters_for_ordered_reads():
    fs = [{"uuid": "u0"}, {"uuid": "u1"}]
    s, log = _shadow(
        fs={"file_manifest": fs}, sql={"file_manifest": list(reversed(fs))}
    )
    s.file_manifest("orders")
    assert s.counts["file_manifest"]["differences"] == 1


def test_order_does_not_matter_for_instance_dirs():
    s, log = _shadow(
        fs={"instance_dirs": ["a", "b", "c"]}, sql={"instance_dirs": ["c", "a", "b"]}
    )
    assert s.instance_dirs("/ar/acme/run") == ["a", "b", "c"]
    assert log.warnings == []
    assert s.counts["instance_dirs"]["matches"] == 1


def test_instance_dirs_still_differ_by_content():
    s, log = _shadow(
        fs={"instance_dirs": ["a", "b"]}, sql={"instance_dirs": ["a", "b", "b"]}
    )
    s.instance_dirs("/ar/acme/run")
    assert s.counts["instance_dirs"]["differences"] == 1


def test_describe_of_equal_lists():
    assert (
        ShadowReferenceSource.describe(fs=["a", "b"], sql=["a", "b"])
        == "lengths 2 vs 2, same items"
    )


# ===================
# errors
# ===================


@pytest.mark.parametrize("method", list(CALLS))
def test_a_sql_error_is_logged_counted_and_raised(method):
    boom = RuntimeError("database went away")
    s, log = _shadow(fs={method: ["a"]}, sql={method: boom})
    with pytest.raises(RuntimeError) as e:
        _call(s, method)
    assert e.value is boom
    assert len(log.errors) == 1
    assert log.errors[0].startswith(f"shadow: SQL {method}(")
    assert "database went away" in log.errors[0]
    assert log.exceptions == [boom]
    assert s.counts[method] == {
        "reads": 1,
        "matches": 0,
        "differences": 0,
        "sql_errors": 1,
    }


@pytest.mark.parametrize("method", list(CALLS))
def test_a_primary_error_raises_without_reading_sql(method):
    s, log = _shadow(fs={method: ValueError("bad name")}, sql={method: ["a"]})
    with pytest.raises(ValueError):
        _call(s, method)
    assert s.secondary.calls == []
    assert log.errors == []
    assert s.counts == {}
