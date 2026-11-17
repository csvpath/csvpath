import os

import pytest

from csvpath import CsvPaths
from csvpath.references.reference_estimate_3 import EXACT, UPPER_BOUND, ReferenceEstimate3
from csvpath.references.reference_finder_factory_3 import ReferenceFinderFactory3
from tests.references.cost.read_counter import ReadCounter

#
# the RESULTS cost estimate against the read counter, on the corpus
# (references_v3_cost_estimates.md; 3 groups, 11 runs, 23 instances)
#
CORPUS_CONFIG = os.path.join(os.path.dirname(__file__), "..", "..", "corpus", "config", "config.ini")


@pytest.fixture(scope="module")
def csvpaths():
    previous = os.environ.get("CSVPATH_CONFIG_PATH")
    os.environ["CSVPATH_CONFIG_PATH"] = os.path.abspath(CORPUS_CONFIG)
    try:
        yield CsvPaths()
    finally:
        if previous is None:
            os.environ.pop("CSVPATH_CONFIG_PATH", None)
        else:
            os.environ["CSVPATH_CONFIG_PATH"] = previous


def _finder(csvpaths, reference):
    return ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=csvpaths)


def _measured(csvpaths, reference):
    finder = _finder(csvpaths, reference)
    with ReadCounter.for_csvpaths(csvpaths) as query:
        selection = finder.query()
    with ReadCounter.for_csvpaths(csvpaths) as resolve:
        finder.resolve_from(selection)
    return dict(query.reads), dict(resolve.reads)


EXACT_SHAPES = [
    "$validate_orders.results.:last().*",
    "$validate_orders.results.:last()",
    "$*.results.:all().*:valid(:true())",
    '$validate_orders.results.:flatten().*:errors():idchain("add[0]")',
    '$validate_orders.results.:having(:errors(:idchain("add[0]")))',
    "$validate_orders.results.:last().*:uuid()",
    "$*.results.:last().*",
    "$validate_orders.results.:first().*",
]


@pytest.mark.parametrize("reference", EXACT_SHAPES)
def test_the_estimate_predicts_the_reads(csvpaths, reference):
    est = _finder(csvpaths, reference).estimate()
    assert (est.query_reads, est.resolve_reads) == _measured(csvpaths, reference)


def test_the_estimate_reads_only_the_ledger(csvpaths):
    finder = _finder(csvpaths, "$*.results.:all().*:valid(:true())")
    with ReadCounter.for_csvpaths(csvpaths) as counter:
        finder.estimate()
    assert dict(counter.reads) == {"ledger": 1}


def test_several_whole_files_would_raise(csvpaths):
    est = _finder(csvpaths, "$*.results.:last().*:errors()").estimate()
    assert est.would_raise and "5.3" in est.would_raise
    # it raises before reading anything at resolve
    assert est.query_reads["instance_manifest"] == 8 and est.resolve_reads == {}


def test_selecting_records_does_not_raise(csvpaths):
    est = _finder(csvpaths, '$*.results.:last().*:errors():idchain("add[0]")').estimate()
    assert est.would_raise is None


def test_a_time_window_is_an_upper_bound(csvpaths):
    est = _finder(csvpaths, "$validate_orders.results.:flatten():yesterday().*:errors()").estimate()
    assert all(r.basis == UPPER_BOUND for r in est.reads if r.kind != "ledger")
    assert any("time window" in w for w in est.why)
    assert est.estimated
    # the window may leave one run, so several files only may raise
    assert est.would_raise.startswith("may raise")


def test_having_by_content_is_an_upper_bound_and_explained(csvpaths):
    est = _finder(csvpaths, '$validate_orders.results.:having(:errors(:idchain("add[0]")))').estimate()
    errors = [r for r in est.reads if r.kind == "errors_json"]
    assert errors and errors[0].basis == UPPER_BOUND
    assert any(":having() by content" in w for w in est.why)


def test_star_says_how_many_groups(csvpaths):
    est = _finder(csvpaths, "$*.results.:all().*:valid(:true())").estimate()
    assert any("3 named-results groups" in w for w in est.why)


def test_the_backend_and_weights_are_reported(csvpaths):
    d = _finder(csvpaths, "$validate_orders.results.:last()").estimate().to_dict()
    assert d["backend"] == "local" and d["sql"] is False
    assert d["max_score"] == ReferenceEstimate3.MAX_SCORE


def test_the_ledger_read_is_exact(csvpaths):
    est = _finder(csvpaths, "$validate_orders.results.:last()").estimate()
    assert [r for r in est.reads if r.kind == "ledger"][0].basis == EXACT


def test_an_unknown_group_reads_only_the_ledger(csvpaths):
    est = _finder(csvpaths, "$nope.results.:last().*").estimate()
    assert est.query_reads == {"ledger": 1}
