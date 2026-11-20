"""The CLI's "show the SQL for a reference" item resolves a reference or an
expression inside a SQL capture and prints the trace. With [references]
sql off there is no SQL, and it says so. The CLI and the source are fakes."""

import builtins
from contextlib import contextmanager

import pytest

from csvpath.cli import reference_runner as rr
from csvpath.cli.reference_runner import ReferenceRunner
from csvpath.references.reference_exceptions_3 import ReferenceException3
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


class _RaisingFinder(_Finder):
    """queries fine, then raises on resolve, as a legal reference to
    several files does (compendium 5.3)"""

    def resolve(self):
        raise ReferenceException3("cannot resolve more than one file at once")


def _no_error_menu(monkeypatch):
    seen = []

    def _handle(cli, e):
        seen.append(e)
        return False

    monkeypatch.setattr(rr.erut, "handle", _handle)
    return seen


def test_a_resolve_that_raises_still_shows_its_sql(monkeypatch, capsys):
    # it printed only the error menu (name_one gap review, 2026-11-19)
    monkeypatch.setattr(builtins, "input", lambda prompt="": "")
    monkeypatch.setattr(
        rr.ReferenceFinderFactory3,
        "for_reference",
        lambda *, reference, csvpaths: _RaisingFinder(),
    )
    seen = _no_error_menu(monkeypatch)
    _ask(monkeypatch, "$a.results.:all().:manifest()")
    ReferenceRunner(_Cli(_Tracing()))._show_sql()
    out = capsys.readouterr().out
    assert "resolve() raised ReferenceException3: cannot resolve more than one file" in out
    assert "The SQL that ran before it: 1 statements" in out
    assert "$a.files.:last() query: SELECT manifest_entry FROM named_file" in out
    # the usual error handling still runs
    assert len(seen) == 1


def test_a_parse_error_shows_no_sql(monkeypatch, capsys):
    # nothing was captured, so there is no SQL section
    monkeypatch.setattr(builtins, "input", lambda prompt="": "")
    seen = _no_error_menu(monkeypatch)
    _ask(monkeypatch, "$a.files.")
    ReferenceRunner(_Cli(_Tracing()))._show_sql()
    out = capsys.readouterr().out
    assert "The SQL that ran before it" not in out
    assert len(seen) == 1
