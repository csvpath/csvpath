"""The CLI's "estimate a reference" item prints an estimate's summary, for
a plain reference and for an expression. The CLI is a fake."""

import builtins

import pytest

from csvpath.cli import reference_runner as rr
from csvpath.cli.reference_runner import ReferenceRunner


class _Estimate:
    def summary(self):
        return "SUMMARY"


class _Finder:
    def estimate(self):
        return _Estimate()


class _Cli:
    def __init__(self):
        self.csvpaths = object()

    def clear(self):
        pass

    def action(self, text):
        pass


@pytest.fixture
def runner(monkeypatch, capsys):
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


def test_a_reference_is_estimated(runner, monkeypatch, capsys):
    _ask(monkeypatch, "$a.files.:last()")
    ReferenceRunner(_Cli())._estimate()
    assert runner == [("reference", "$a.files.:last()")]
    assert "SUMMARY" in capsys.readouterr().out


def test_an_expression_is_estimated(runner, monkeypatch, capsys):
    _ask(monkeypatch, "$a.files.:last() UNION $b.files.:last()")
    ReferenceRunner(_Cli())._estimate()
    assert runner[0][0] == "expression"
    assert "SUMMARY" in capsys.readouterr().out


def test_nothing_entered_does_nothing(runner, monkeypatch):
    _ask(monkeypatch, "")
    ReferenceRunner(_Cli())._estimate()
    assert runner == []
