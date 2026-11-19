#
# the SQL trace for references (David, 2026-11-19): capture the SQL the v3
# references run when [references] sql is on or shadow, for analysing how
# simple or complex it is. Low-level pieces first, then a real local
# sqlite database through the SQL source.
#
import pytest

from csvpath.references.reference_finder_factory_3 import ReferenceFinderFactory3
from csvpath.references.sources.filesystem_reference_source import (
    FilesystemReferenceSource,
)
from csvpath.references.sources.sql_trace import SqlStatement, SqlTrace, SqlTracing
from csvpath.util.config_exception import ConfigurationException

from tests.references import test_sql_reference_source as sqlt


def _statement(sql="SELECT 1", params=None, rows=1, ms=0.5, phase="query"):
    return SqlStatement(
        reference="$a.files.:last()",
        phase=phase,
        sql=sql,
        params=params or {},
        rows=rows,
        ms=ms,
    )


class _Logger:
    def __init__(self):
        self.infos = []

    def info(self, msg, *args):
        self.infos.append(msg % args if args else msg)


class _Config:
    def __init__(self):
        self.values = {}

    def get(self, *, section, name):
        return self.values.get((section, name))


class _CsvPaths:
    def __init__(self):
        self.config = _Config()
        self.logger = _Logger()


# ===================
# SqlTrace
# ===================


def test_an_empty_trace_says_no_sql_ran():
    assert "no SQL ran" in SqlTrace().summary()


def test_the_summary_counts_statements_repeats_rows_and_time():
    trace = SqlTrace()
    trace.add(_statement(sql="SELECT a", params={"p": 1}, rows=2, ms=1.0))
    trace.add(_statement(sql="SELECT a", params={"p": 1}, rows=2, ms=1.0))
    trace.add(_statement(sql="SELECT a", params={"p": 2}, rows=0, ms=0.5))
    trace.add(_statement(sql="SELECT b", rows=1, ms=0.5))
    assert trace.repeats == 1
    assert trace.summary() == "4 statements, 2 distinct, 1 repeats, 5 rows, 3.0 ms"


def test_add_takes_only_statements():
    with pytest.raises(TypeError):
        SqlTrace().add("SELECT 1")


def test_to_dicts_and_line():
    s = _statement(sql="SELECT a", params={"p": 1}, rows=2, ms=1.25)
    assert SqlTrace(statements=[s]).to_dicts()[0]["sql"] == "SELECT a"
    assert s.line() == "$a.files.:last() query: SELECT a | {'p': 1} | 2 rows | 1.2 ms"


# ===================
# SqlTracing
# ===================


def test_tracing_needs_csvpaths():
    with pytest.raises(ValueError):
        SqlTracing(csvpaths=None)


def test_a_phase_is_required():
    with pytest.raises(ValueError):
        SqlTracing(csvpaths=_CsvPaths()).set_context(reference="$a", phase="")


@pytest.mark.parametrize(
    "value, on",
    [(None, False), ("off", False), ("on", True), ("ON ", True), ("yes", True)],
)
def test_the_logging_switch(value, on):
    paths = _CsvPaths()
    paths.config.values[("references", "sql_trace")] = value
    assert SqlTracing(csvpaths=paths).logging_on() is on


def test_a_bad_switch_value_raises():
    paths = _CsvPaths()
    paths.config.values[("references", "sql_trace")] = "maybe"
    with pytest.raises(ConfigurationException):
        SqlTracing(csvpaths=paths).logging_on()


def test_the_switch_is_read_each_time_not_cached():
    paths = _CsvPaths()
    tracing = SqlTracing(csvpaths=paths)
    tracing.set_context(reference="$a", phase="query")
    tracing.record(sql="SELECT 1", params={}, rows=0, started=0.0)
    assert paths.logger.infos == []
    paths.config.values[("references", "sql_trace")] = "on"
    tracing.record(sql="SELECT  2\n FROM t", params={"x": 1}, rows=3, started=0.0)
    assert len(paths.logger.infos) == 1
    assert (
        "SQL trace: $a query: SELECT 2 FROM t | {'x': 1} | 3 rows"
        in paths.logger.infos[0]
    )
    paths.config.values[("references", "sql_trace")] = "off"
    tracing.record(sql="SELECT 3", params={}, rows=0, started=0.0)
    assert len(paths.logger.infos) == 1


def test_a_capture_sees_only_its_block():
    tracing = SqlTracing(csvpaths=_CsvPaths())
    tracing.set_context(reference="$a", phase="query")
    tracing.record(sql="SELECT before", params={}, rows=0, started=0.0)
    with tracing.capture() as outer:
        tracing.record(sql="SELECT one", params={}, rows=0, started=0.0)
        with tracing.capture() as inner:
            tracing.record(sql="SELECT two", params={}, rows=0, started=0.0)
    tracing.record(sql="SELECT after", params={}, rows=0, started=0.0)
    assert [s.sql for s in outer.statements] == ["SELECT one", "SELECT two"]
    assert [s.sql for s in inner.statements] == ["SELECT two"]
    assert not tracing.active


def test_a_query_starts_a_new_total():
    paths = _CsvPaths()
    paths.config.values[("references", "sql_trace")] = "on"
    tracing = SqlTracing(csvpaths=paths)
    tracing.set_context(reference="$a", phase="query")
    tracing.record(sql="SELECT 1", params={}, rows=1, started=0.0)
    tracing.set_context(reference="$a", phase="resolve")
    tracing.record(sql="SELECT 1", params={}, rows=1, started=0.0)
    tracing.log_total()
    assert paths.logger.infos[-1].startswith(
        "SQL trace: $a total: 2 statements, 1 distinct, 1 repeats"
    )
    tracing.set_context(reference="$a", phase="query")
    assert tracing.current.statements == []


def test_no_total_when_logging_is_off():
    paths = _CsvPaths()
    tracing = SqlTracing(csvpaths=paths)
    tracing.set_context(reference="$a", phase="query")
    tracing.record(sql="SELECT 1", params={}, rows=1, started=0.0)
    tracing.log_total()
    assert paths.logger.infos == []


# ===================
# a real local sqlite database
# ===================


@pytest.fixture
def paths(tmp_path):
    sqlt._clear_engine()
    p = sqlt._paths(tmp_path)
    for n in range(3):
        sqlt._register(p, tmp_path, n=n)
    sqlt._load(p, tmp_path)
    yield p
    sqlt._clear_engine()


def _finder(paths, reference):
    return ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=paths)


def test_sql_on_captures_each_read_with_its_phase(paths):
    sqlt._mode(paths, "on")
    finder = _finder(paths, '$*.files.:manifest():type("csv")')
    with finder.capture_sql() as trace:
        results = finder.resolve()
    assert len(results) == 3
    assert trace.statements
    assert {s.phase for s in trace.statements} == {"query", "resolve"}
    assert all(
        s.reference == '$*.files.:manifest():type("csv")' for s in trace.statements
    )
    assert all(s.sql.startswith("SELECT") for s in trace.statements)
    ledger = [s for s in trace.statements if "FROM named_file_ledger" in s.sql]
    assert ledger and all(s.rows == 3 for s in ledger)


def test_the_sql_is_the_dialects_with_its_parameters(paths):
    sqlt._mode(paths, "on")
    finder = _finder(paths, "$orders.files.:last()")
    with finder.capture_sql() as trace:
        finder.query()
    statement = trace.statements[0]
    assert "WHERE named_file.files_root = ?" in statement.sql
    assert "orders" in statement.params.values()


def test_sql_off_captures_nothing(paths):
    sqlt._mode(paths, "off")
    finder = _finder(paths, "$orders.files.:last()")
    assert isinstance(finder.source, FilesystemReferenceSource)
    with finder.capture_sql() as trace:
        finder.resolve()
    assert trace.statements == []
    assert "no SQL ran" in trace.summary()


def test_shadow_captures_the_sql_side(paths):
    sqlt._mode(paths, "shadow")
    finder = _finder(paths, "$orders.files.:last()")
    with finder.capture_sql() as trace:
        finder.resolve()
    assert trace.statements


def test_writes_are_not_traced(paths, tmp_path):
    # the SQL listeners share the engine; only reference reads are recorded
    sqlt._mode(paths, "on")
    finder = _finder(paths, "$orders.files.:last()")
    with finder.capture_sql() as trace:
        sqlt._register(paths, tmp_path, n=9)
    assert trace.statements == []


def test_the_log_switch_can_be_turned_on_while_running(paths):
    sqlt._mode(paths, "on")
    logged = []
    real_info = paths.logger.info
    paths.logger.info = lambda msg, *args: logged.append(msg % args if args else msg)
    try:
        _finder(paths, "$orders.files.:last()").resolve()
        assert logged == []
        paths.config.add_to_config("references", "sql_trace", "on")
        _finder(paths, "$orders.files.:last()").resolve()
        assert any(
            line.startswith("SQL trace: $orders.files.:last() query: SELECT")
            for line in logged
        )
        assert logged[-1].startswith("SQL trace: $orders.files.:last() total: ")
        count = len(logged)
        paths.config.add_to_config("references", "sql_trace", "off")
        _finder(paths, "$orders.files.:last()").resolve()
        assert len(logged) == count
    finally:
        paths.logger.info = real_info


# ===================
# totals through the finders (reviewer on #775)
# ===================


def _log(paths):
    logged = []
    paths.logger.info = lambda msg, *args: logged.append(msg % args if args else msg)
    paths.config.add_to_config("references", "sql_trace", "on")
    return logged


def _totals(logged):
    return [line for line in logged if " total: " in line]


@pytest.mark.parametrize(
    "reference", ['$*.files.:manifest():type("csv")', "$orders.csvpaths.:all()"]
)
def test_resolve_each_logs_one_total(paths, reference):
    # FILES overrides resolve_each(); it logged one growing total per result
    sqlt._mode(paths, "on")
    logged = _log(paths)
    finder = _finder(paths, reference)
    selection = finder.query()
    finder.resolve_each(selection)
    assert len(_totals(logged)) == 1


def test_a_second_resolve_from_starts_its_total_at_zero(paths):
    sqlt._mode(paths, "on")
    logged = _log(paths)
    finder = _finder(paths, '$*.files.:manifest():type("csv")')
    selection = finder.query()
    finder.resolve_from(selection)
    finder.resolve_from(selection)
    first, second = _totals(logged)
    # the first total includes the query's reads; the second only resolve's
    assert first != second
    with finder.capture_sql() as trace:
        finder.resolve_from(selection)
    # the same reads as a fresh capture of one resolve_from (timings vary)
    assert second.split(" rows, ")[0].endswith(trace.summary().split(" rows, ")[0])


def test_an_estimate_is_traced_and_totalled(paths):
    sqlt._mode(paths, "on")
    logged = _log(paths)
    finder = _finder(paths, "$orders.files.:last()")
    with finder.capture_sql() as trace:
        finder.estimate()
    assert trace.statements
    assert {s.phase for s in trace.statements} == {"estimate"}
    assert len(_totals(logged)) == 1


def test_a_read_after_a_total_is_not_tagged_with_the_last_reference(paths):
    sqlt._mode(paths, "on")
    finder = _finder(paths, "$orders.files.:last()")
    finder.resolve()
    with finder.capture_sql() as trace:
        finder.source.files_ledger()
    assert [(s.reference, s.phase) for s in trace.statements] == [(None, None)]


def test_an_expression_captures_both_sides(paths):
    from csvpath.references.reference_expression_3 import ReferenceExpression3

    sqlt._mode(paths, "on")
    logged = _log(paths)
    expression = ReferenceExpression3.from_string(
        expression="$orders.files.:first() UNION $orders.files.:last()", csvpaths=paths
    )
    with expression.capture_sql() as trace:
        expression.resolve()
    assert {s.reference for s in trace.statements} == {
        "$orders.files.:first()",
        "$orders.files.:last()",
    }
    # one total per side, none for the whole expression
    assert len(_totals(logged)) == 2


def test_an_expression_with_sql_off_captures_nothing(paths):
    from csvpath.references.reference_expression_3 import ReferenceExpression3

    sqlt._mode(paths, "off")
    expression = ReferenceExpression3.from_string(
        expression="$orders.files.:first() UNION $orders.files.:last()", csvpaths=paths
    )
    with expression.capture_sql() as trace:
        expression.resolve()
    assert trace.statements == []
