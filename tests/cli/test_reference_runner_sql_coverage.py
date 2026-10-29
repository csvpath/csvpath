"""The "check SQL coverage" item in the CLI's run reference expressions
menu (step 6, PR 2). It prints ReferencesSqlCoverage's report.

The CLI is a fake: ask() returns scripted answers and records the choices
it was offered, and input() is patched, so nothing interactive runs. The
end-to-end tests use real sources over SQLite in pytest's tmp_path.
"""

import builtins

import pytest

from csvpath import CsvPaths
from csvpath.cli import reference_runner as rr
from csvpath.cli.const import Const
from csvpath.cli.reference_runner import ReferenceRunner
from csvpath.references.sources.references_sql_coverage import (
    ReferencesSqlCoverage,
)
from csvpath.util.box import Box

ITEM = "check SQL coverage"


class _Cli:
    def __init__(self, *, csvpaths, answers: list):
        self.csvpaths = csvpaths
        self.answers = list(answers)
        self.offered = []
        self.actions = []

    def ask(self, choices, q=None):
        self.offered.append(list(choices))
        return self.answers.pop(0)

    def clear(self):
        pass

    def action(self, text):
        self.actions.append(text)


@pytest.fixture
def prompts(monkeypatch):
    seen = []

    def _input(prompt=""):
        seen.append(prompt)
        return ""

    monkeypatch.setattr(builtins, "input", _input)
    return seen


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
        value=f"sqlite:///{tmp_path / 'cli.db'}",
    )
    return p


@pytest.fixture
def real(tmp_path):
    _clear_engine()
    yield tmp_path
    _clear_engine()


def _register(p: CsvPaths, tmp_path, *, n: int) -> None:
    data = tmp_path / f"orders_{n}.csv"
    data.write_text(f"id,amount\n{n},10\n", encoding="utf-8")
    p.file_manager.add_named_file(name="orders", path=str(data))


def _check(p: CsvPaths):
    cli = _Cli(csvpaths=p, answers=[ITEM, Const.CANCEL2])
    ReferenceRunner(cli).menu()
    return cli


# ===================
# the menu
# ===================


def test_the_menu_offers_the_item_before_cancel():
    cli = _Cli(csvpaths=None, answers=[Const.CANCEL2])
    ReferenceRunner(cli).menu()
    assert cli.offered == [
        [
            "rerun recent",
            "new expression",
            "browse functions",
            ITEM,
            Const.CANCEL2,
        ]
    ]


def test_the_item_comes_back_to_the_references_menu(monkeypatch):
    calls = []
    monkeypatch.setattr(
        ReferenceRunner, "_check_sql_coverage", lambda self: calls.append(1)
    )
    cli = _Cli(csvpaths=None, answers=[ITEM, ITEM, Const.CANCEL2])
    ReferenceRunner(cli).menu()
    assert calls == [1, 1]
    assert len(cli.offered) == 3


@pytest.mark.parametrize(
    "choice,method",
    [
        ("rerun recent", "_rerun_recent"),
        ("new expression", "_edit_and_run"),
    ],
)
def test_the_other_choices_are_unchanged(monkeypatch, choice, method):
    calls = []
    monkeypatch.setattr(ReferenceRunner, method, lambda self, *a: calls.append(a))
    monkeypatch.setattr(
        ReferenceRunner,
        "_check_sql_coverage",
        lambda self: pytest.fail("coverage was not chosen"),
    )
    cli = _Cli(csvpaths=None, answers=[choice])
    ReferenceRunner(cli).menu()
    assert len(calls) == 1
    #
    # one-shot actions: back to the main menu, not this one
    #
    assert len(cli.offered) == 1


def test_browse_functions_is_unchanged(monkeypatch):
    calls = []
    monkeypatch.setattr(
        rr.ReferenceFunctionLister, "list_functions", lambda self: calls.append(1)
    )
    cli = _Cli(csvpaths=None, answers=["browse functions", Const.CANCEL2])
    ReferenceRunner(cli).menu()
    assert calls == [1]
    assert len(cli.offered) == 2


# ===================
# the report, end to end
# ===================


def test_a_covered_config(real, prompts, capsys):
    p = _paths(real)
    _register(p, real, n=0)
    cli = _check(p)
    out = capsys.readouterr().out
    assert "references SQL coverage" in out
    assert "COVERED: [references] sql = on will see everything" in out
    assert "NOT COVERED" not in out
    assert cli.actions == ["Checking SQL coverage\n"]
    assert prompts == ["\nHit return to continue. "]


def test_a_late_start(real, prompts, capsys):
    p = _paths(real, groups="")
    _register(p, real, n=0)
    p.config.add_to_config(section="listeners", key="groups", value="sql")
    _register(p, real, n=1)
    _check(p)
    out = capsys.readouterr().out
    assert "NOT COVERED" in out
    assert "SQL was switched on after they were written" in out
    assert "by name: orders 1" in out


def test_a_config_without_sql(real, prompts, capsys):
    p = _paths(real, groups="")
    p.config.add_to_config(section="sql", key="dialect", value="")
    _check(p)
    out = capsys.readouterr().out
    assert "SQL cannot be used, so it was not read:" in out
    assert "[sql] dialect is not set" in out
    assert "NOT READY" in out


def test_the_printed_report_is_the_format_of_the_report(real, prompts, capsys):
    p = _paths(real)
    _register(p, real, n=0)
    _check(p)
    out = capsys.readouterr().out
    expected = ReferencesSqlCoverage.format(
        report=ReferencesSqlCoverage(csvpaths=p).report()
    )
    assert expected in out


# ===================
# errors
# ===================


def test_an_error_goes_to_the_error_menu(monkeypatch, prompts):
    boom = RuntimeError("boom")

    def report(self):
        raise boom

    handled = []
    monkeypatch.setattr(ReferencesSqlCoverage, "report", report)
    monkeypatch.setattr(
        rr.erut, "handle", staticmethod(lambda cli, e: handled.append(e) or False)
    )
    cli = _check(CsvPaths())
    assert handled == [boom]
    #
    # the error menu's own continue returns at once, then back to the
    # references menu
    #
    assert prompts == []
    assert len(cli.offered) == 2


def test_the_error_menu_logs_the_error(monkeypatch):
    def report(self):
        raise RuntimeError("boom")

    logged = []
    p = CsvPaths()
    monkeypatch.setattr(ReferencesSqlCoverage, "report", report)
    monkeypatch.setattr(type(p), "logger", property(lambda s: _Logger(logged)))
    #
    # the error menu reads one answer: return, to continue
    #
    monkeypatch.setattr(builtins, "input", lambda prompt="": "")
    _check(p)
    assert [str(e) for e in logged] == ["boom"]


class _Logger:
    def __init__(self, logged):
        self.logged = logged

    def error(self, e):
        self.logged.append(e)


def test_ctrl_c_cancels_back_to_the_menu(monkeypatch, prompts, capsys):
    def report(self):
        raise KeyboardInterrupt()

    monkeypatch.setattr(ReferencesSqlCoverage, "report", report)
    try:
        cli = _check(CsvPaths())
    except KeyboardInterrupt:
        pytest.fail("ctrl-c escaped the coverage check")
    assert "Cancelled." in capsys.readouterr().out
    assert prompts == []
    assert len(cli.offered) == 2
