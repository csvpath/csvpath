"""The CLI's run reference expressions menu dispatches a line through
ReferenceExpressionParser3 (issue #444): an expression goes to
ReferenceExpression3.from_tree(), a plain reference to the finder
factory. The CLI is a fake and nothing resolves."""

import builtins

import pytest

from csvpath.cli import reference_runner as rr
from csvpath.cli.reference_runner import ReferenceRunner
from csvpath.references.reference_results_3 import ReferenceResults3


class _Cli:
    def __init__(self):
        self.csvpaths = object()
        self.actions = []

    def clear(self):
        pass

    def action(self, text):
        self.actions.append(text)


class _Finder:
    def resolve(self):
        return ReferenceResults3()


@pytest.fixture
def runner(monkeypatch):
    calls = []

    def _from_tree(*, tree, csvpaths):
        calls.append(("expression", tree))
        return _Finder()

    def _for_reference(*, reference, csvpaths):
        calls.append(("reference", reference))
        return _Finder()

    monkeypatch.setattr(rr.ReferenceExpression3, "from_tree", _from_tree)
    monkeypatch.setattr(rr.ReferenceFinderFactory3, "for_reference", _for_reference)
    monkeypatch.setattr(builtins, "input", lambda prompt="": "")
    r = ReferenceRunner(_Cli())
    monkeypatch.setattr(r, "_remember", lambda expression: None)
    monkeypatch.setattr(r, "_display", lambda results: None)
    return r, calls


def test_an_expression_goes_to_from_tree(runner):
    r, calls = runner
    r._run("($a.files.:last() union $b.files.:last()) SUBTRACT $c.files.:first()")
    assert calls == [
        (
            "expression",
            (
                ("$a.files.:last()", "union", "$b.files.:last()"),
                "subtract",
                "$c.files.:first()",
            ),
        )
    ]


def test_a_grouped_plain_reference_goes_to_the_factory_unwrapped(runner):
    r, calls = runner
    r._run("( $a.files.:last() )")
    assert calls == [("reference", "$a.files.:last()")]


def test_a_quoted_operator_is_a_plain_reference(runner):
    # the old split was quote-blind and cut this reference in two
    r, calls = runner
    r._run('$a.files.:regex("x UNION y")')
    assert calls == [("reference", '$a.files.:regex("x UNION y")')]


def test_a_plain_reference_goes_to_the_factory(runner):
    r, calls = runner
    r._run("$a.files.:last()")
    assert calls == [("reference", "$a.files.:last()")]
