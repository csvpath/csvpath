"""The CLI's "show the SQL for a reference" item resolves a reference or an
expression inside a SQL capture and prints the trace. With [references]
sql off there is no SQL, and it says so. The CLI and the source are fakes."""

import builtins
from contextlib import contextmanager

import pytest

from csvpath.cli import reference_runner as rr
from csvpath.cli.reference_runner import ReferenceRunner
from csvpath.references.sources.sql_trace import SqlStatement, SqlTrace


class _Tracing:
    @contextmanager
    def capture(self):
        trace = SqlTrace()
        trace.add(
            SqlStatement(
                reference="$a.files.:last()",
                phase="query",
                sql="SELECT manifest_entry FROM named_file",
                params={"p": "a"},
                rows=2,
                ms=0.3,
            )
        )
        yield trace


class _Source:
    def __init__(self, tracing):
        self.sql_tracing = tracing


class _CsvPaths:
    def __init__(self, tracing):
        self.reference_source = _Source(tracing)


class _Cli:
    def __init__(self, tracing):
        self.csvpaths = _CsvPaths(tracing)

    def clear(self):
        pass


class _Finder:
    def resolve(self):
        return [1, 2]

    def capture_sql(self):
        return _Tracing().capture()


@pytest.fixture
def calls(monkeypatch):
    calls = []
    monkeypatch.setattr(builtins, "input", lambda prompt="": "")

    def _for_reference(*, reference, csvpaths):
        calls.append(("reference", reference))
        return _Finder()

    def _from_tree(*, tree, csvpaths):
        calls.append(("expression", tree))
        return _Finder()

    monkeypatch.setattr(rr.ReferenceFinderFactory3, "for_reference", _for_reference)
    monkeypatch.setattr(rr.ReferenceExpression3, "from_tree", _from_tree)
    return calls


def _ask(monkeypatch, text):
    class _Asker:
        def __init__(self, *args, **kwargs):
            pass

        def ask(self):
            return text

    monkeypatch.setattr(rr, "Asker", _Asker)


def test_sql_off_says_there_is_no_sql(calls, monkeypatch, capsys):
    _ask(monkeypatch, "$a.files.:last()")
    ReferenceRunner(_Cli(None))._show_sql()
    assert calls == []
    assert "there is no SQL to show" in capsys.readouterr().out


def test_a_reference_prints_its_trace(calls, monkeypatch, capsys):
    _ask(monkeypatch, "$a.files.:last()")
    ReferenceRunner(_Cli(_Tracing()))._show_sql()
    assert calls == [("reference", "$a.files.:last()")]
    out = capsys.readouterr().out
    assert "2 results; 1 statements, 1 distinct, 0 repeats, 2 rows" in out
    assert "$a.files.:last() query: SELECT manifest_entry FROM named_file" in out


def test_an_expression_is_traced_too(calls, monkeypatch, capsys):
    _ask(monkeypatch, "$a.files.:last() UNION $b.files.:last()")
    ReferenceRunner(_Cli(_Tracing()))._show_sql()
    assert calls[0][0] == "expression"


def test_nothing_entered_does_nothing(calls, monkeypatch):
    _ask(monkeypatch, "")
    ReferenceRunner(_Cli(_Tracing()))._show_sql()
    assert calls == []
