#
# ':name(...)' as root_major (compendium 3.8: "a name that may include
# variable interpolation or be the string form of a variable"; NRE
# '$:name("{@where} orders").files.:flatten()'). Every finder raised
# ":name() is not a legal root_major function" until the name_one gap
# review (item E). It resolves to the literal name, so the reference reads
# as if the name were written plainly; ':name(/re/)' is ':regex()'.
#
import os

import pytest

from csvpath import CsvPaths
from csvpath.references.reference_3 import FunctionCall3, Regex3
from csvpath.references.reference_estimate_3 import QUERY, RESOLVE
from csvpath.references.reference_exceptions_3 import ReferenceException3
from csvpath.references.reference_finder_factory_3 import ReferenceFinderFactory3
from csvpath.references.reference_parser_3 import ReferenceParser3
from tests.references.cost.read_counter import ReadCounter
from tests.references.cost.test_results_estimate_soundness_3 import (
    CORPUS_CONFIG,
    _problems,
)


@pytest.fixture(scope="module")
def corpus():
    previous = os.environ.get("CSVPATH_CONFIG_PATH")
    os.environ["CSVPATH_CONFIG_PATH"] = os.path.abspath(CORPUS_CONFIG)
    try:
        yield CsvPaths()
    finally:
        if previous is None:
            os.environ.pop("CSVPATH_CONFIG_PATH", None)
        else:
            os.environ["CSVPATH_CONFIG_PATH"] = previous


def _finder(corpus, reference: str, value=None):
    finder = ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=corpus)
    if value is not None:
        finder.set_variable("w", value=value)
    return finder


def _results(corpus, reference: str, value=None) -> list:
    return [
        (str(r.path), r.uuid) for r in _finder(corpus, reference, value).query().results
    ]


class TestReplaceRootMajor:
    def test_takes_a_name_or_a_function(self, corpus):
        parsed = ReferenceParser3(string='$:name("x").files.*', csvpaths=corpus).parsed
        parsed.replace_root_major("orders")
        assert parsed.root_major == "orders"
        parsed.replace_root_major(FunctionCall3(name="regex", arg=Regex3(pattern="^o")))
        assert parsed.root_major.name == "regex"

    @pytest.mark.parametrize(
        "value,error", [(None, ValueError), ("  ", ValueError), (3, TypeError)]
    )
    def test_rejects_anything_else(self, corpus, value, error):
        parsed = ReferenceParser3(string="$orders.files.*", csvpaths=corpus).parsed
        with pytest.raises(error):
            parsed.replace_root_major(value)


SAME_AS = [
    ('$:name("orders").files.:flatten()', None, "$orders.files.:flatten()"),
    ('$:name("{@w}").files.:flatten()', "orders", "$orders.files.:flatten()"),
    (
        "$:name(@w).files.:flatten().:last()",
        "orders",
        "$orders.files.:flatten().:last()",
    ),
    (
        "$:name(@w).csvpaths.:last()",
        "validate_orders",
        "$validate_orders.csvpaths.:last()",
    ),
    (
        "$:name(@w).results.:last()",
        "validate_orders",
        "$validate_orders.results.:last()",
    ),
    ("$:name(/^ord/).files.:flatten()", None, "$:regex(/^ord/).files.:flatten()"),
]


@pytest.mark.parametrize("written,value,same_as", SAME_AS)
def test_reads_as_the_plain_spelling(corpus, written, value, same_as):
    got = _results(corpus, written, value)
    assert got and got == _results(corpus, same_as)


@pytest.mark.parametrize(
    "reference,value,message",
    [
        ("$:name(3).files.:flatten()", None, "takes a name"),
        ("$:name(@w).files.:flatten()", "", "empty name"),
        ("$:name(@w).results.:last()", "  ", "empty name"),
    ],
)
def test_a_name_that_is_not_one_raises(corpus, reference, value, message):
    with pytest.raises(ReferenceException3, match=message):
        _finder(corpus, reference, value).query()


@pytest.mark.parametrize(
    "written,value",
    [(w, v) for w, v, _ in SAME_AS]
    + [("$:name(3).files.:flatten()", None), ("$:name(@w).csvpaths.:last()", "")],
)
def test_the_estimate_keeps_its_contract(corpus, written, value):
    est = _finder(corpus, written, value).estimate()
    finder = _finder(corpus, written, value)
    raised = None
    resolve_reads = {}
    with ReadCounter.for_csvpaths(corpus) as query:
        try:
            selection = finder.query()
        except Exception as e:
            raised = e
    if raised is None:
        with ReadCounter.for_csvpaths(corpus) as resolve:
            try:
                finder.resolve_from(selection)
            except Exception as e:
                raised = e
        resolve_reads = dict(resolve.reads)
    measured = {QUERY: dict(query.reads), RESOLVE: resolve_reads}
    assert _problems(est, measured, raised) == []
