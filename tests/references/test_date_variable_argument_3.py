#
# ':date(@var)' and ':date("{@var}")': Date3.check_valid() checked the
# argument's content before it was resolved, so strptime() raised a raw
# TypeError ("must be str, not Variable3") and ':from(:date(@d))' never
# worked, in any datatype (found by the reviewer on #788). A literal is
# checked when built; a variable's value when it resolves
# (Function3.check_resolved(), #788).
#
import os

import pytest

from csvpath import CsvPaths
from csvpath.references.functions.selectors.date_3 import Date3
from csvpath.references.reference_estimate_3 import QUERY, RESOLVE
from csvpath.references.reference_exceptions_3 import (
    ReferenceException3,
    ReferenceRuntimeException3,
)
from csvpath.references.reference_finder_factory_3 import ReferenceFinderFactory3
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


def _finder(corpus, reference: str, value):
    finder = ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=corpus)
    finder.set_variable("dd", value=value)
    return finder


class TestDate3:
    def test_a_literal_is_checked_when_built(self):
        with pytest.raises(ReferenceException3, match="real calendar date"):
            Date3(arg="2026-13-01").check_valid()

    def test_a_resolved_value_is_checked_when_it_resolves(self):
        f = Date3(arg="2026-01-01")
        f.check_valid()
        f.arg = "soon"
        with pytest.raises(ReferenceException3, match="real calendar date"):
            f.check_resolved()
        f.arg = 20260101
        with pytest.raises(ReferenceException3, match="date string"):
            f.check_resolved()


QUERIES = [
    ("$orders.files.:flatten().:from(:date(@dd)):last()", 1),
    ('$orders.files.:flatten().:from(:date("{@dd}")):last()', 1),
    ("$validate_orders.csvpaths.:from(:date(@dd))", 3),
    ("$validate_orders.results.:flatten():from(:date(@dd)).*", 16),
    # every direction, the bare chain, and inside another time function
    # (reviewer on #790); the corpus is newer than 2020
    ("$orders.files.:flatten().:to(:date(@dd))", 0),
    ("$orders.files.:flatten().:before(:date(@dd))", 0),
    ("$orders.files.:flatten().:after(:date(@dd))", 5),
    ("$validate_orders.results.:flatten():after(:date(@dd)).*", 16),
    ("$validate_orders.results.:flatten():date(@dd).*", 0),
    ("$validate_orders.csvpaths.:date(@dd)", 0),
    ("$validate_orders.results.:flatten():from(:yesterday(:date(@dd))).*", 16),
    ("$orders.files.:flatten().:from(:year(:date(@dd)))", 5),
]


@pytest.mark.parametrize("value", ["2020-01-01", "2020-01-01_10-00-00"])
@pytest.mark.parametrize("reference,count", QUERIES)
def test_a_variable_date_works(corpus, reference, count, value):
    assert len(_finder(corpus, reference, value).query().results) == count


@pytest.mark.parametrize(
    "value,message",
    [
        ("not-a-date", "resolved to 'not-a-date'"),
        ("2026-02-30", "real calendar date"),
        ("", "real calendar date"),
        # through "{@dd}" it arrives as text, so the date check names it
        (20200101, "must be one of: a string|real calendar date"),
        # through "{@dd}" it arrives as text, so the date check names it
        (None, "must be one of: a string|real calendar date"),
    ],
)
@pytest.mark.parametrize("reference,_", QUERIES)
def test_a_variable_that_is_not_a_date_raises_naming_it(
    corpus, reference, _, value, message
):
    # before the matching starts; the estimate predicts it (below)
    finder = _finder(corpus, reference, value)
    with pytest.raises(ReferenceRuntimeException3, match=message):
        finder.query()


@pytest.mark.parametrize("value", ["2020-01-01", "not-a-date"])
@pytest.mark.parametrize("reference,_", QUERIES)
def test_the_estimate_keeps_its_contract(corpus, reference, _, value):
    est = _finder(corpus, reference, value).estimate()
    finder = _finder(corpus, reference, value)
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
