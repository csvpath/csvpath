#
# ':regex(@p)' and ':regex("{@p}")': RegexSelector3 compiled a literal
# pattern when built but never a resolved one, so an invalid pattern from a
# variable matched nothing, silently, in a path segment, and raised a raw
# re.error at root_major (found by the reviewer on #790). check_resolved()
# compiles it once it resolves, before any reads.
#
import os

import pytest

from csvpath import CsvPaths
from csvpath.references.functions.selectors.regex_3 import RegexSelector3
from csvpath.references.reference_exceptions_3 import (
    ReferenceException3,
    ReferenceRuntimeException3,
)
from csvpath.references.reference_finder_factory_3 import ReferenceFinderFactory3
from csvpath.references.reference_estimate_3 import QUERY, RESOLVE
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


def test_a_resolved_invalid_pattern_raises():
    f = RegexSelector3(arg="ok")
    f.check_valid()
    f.arg = "("
    with pytest.raises(ReferenceException3, match="pattern is invalid"):
        f.check_resolved()


REFERENCES = [
    "$orders.files.:regex(@p).:last()",
    # a RESULTS path segment, literal and '$*' (reviewer on #792)
    "$validate_orders.results.:regex(@p)",
    "$*.results.:regex(@p)",
    "$:regex(@p).files.:flatten()",
    '$:regex("{@p}").files.:flatten()',
    "$:regex(@p).csvpaths.:last()",
    "$:regex(@p).results.:last()",
]


@pytest.mark.parametrize("reference", REFERENCES)
def test_an_invalid_variable_pattern_raises_naming_it(corpus, reference):
    finder = ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=corpus)
    finder.set_variable("p", value="(")
    with pytest.raises(ReferenceRuntimeException3, match="resolved to '\\('"):
        finder.query()


@pytest.mark.parametrize(
    "reference,value",
    [(r, "^(orders|validate_orders)$") for r in REFERENCES[3:]]
    + [
        # a path segment matches run names (#647): every one has a '_'
        ("$validate_orders.results.:regex(@p)", "_"),
        ("$*.results.:regex(@p)", "_"),
    ],
)
def test_a_valid_variable_pattern_still_works(corpus, reference, value):
    finder = ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=corpus)
    finder.set_variable("p", value=value)
    assert finder.query().results


@pytest.mark.parametrize(
    "reference",
    [
        "$:last().files.:flatten()",
        "$:year().results.:last()",
        "$:year().csvpaths.:last()",
    ],
)
def test_an_illegal_root_function_is_an_estimate_not_a_crash(corpus, reference):
    # estimate() raised an AttributeError ('Last3' has no 'pattern');
    # query() says it is not a legal root_major function (reviewer on #792)
    finder = ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=corpus)
    assert "not a legal root_major function" in finder.estimate().would_raise
    with pytest.raises(ReferenceException3, match="not a legal root_major function"):
        finder.query()


@pytest.mark.parametrize("value", ["(", "^orders$"])
@pytest.mark.parametrize("reference", REFERENCES)
def test_the_estimate_keeps_its_contract(corpus, reference, value):
    def finder():
        f = ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=corpus)
        f.set_variable("p", value=value)
        return f

    est = finder().estimate()
    f = finder()
    raised = None
    resolve_reads = {}
    with ReadCounter.for_csvpaths(corpus) as query:
        try:
            selection = f.query()
        except Exception as e:
            raised = e
    if raised is None:
        with ReadCounter.for_csvpaths(corpus) as resolve:
            try:
                f.resolve_from(selection)
            except Exception as e:
                raised = e
        resolve_reads = dict(resolve.reads)
    measured = {QUERY: dict(query.reads), RESOLVE: resolve_reads}
    assert _problems(est, measured, raised) == []
