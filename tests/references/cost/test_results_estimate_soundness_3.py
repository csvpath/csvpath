import os

import pytest

from csvpath import CsvPaths
from csvpath.references.reference_estimate_3 import EXACT, QUERY, RESOLVE, UPPER_BOUND
from csvpath.references.reference_finder_factory_3 import ReferenceFinderFactory3
from tests.references.cost.read_counter import ReadCounter
from tests.references.cost.results_shapes import SHAPES

#
# The estimate's contract, checked on every shape: a count marked exact is
# the measured count, an upper bound is never below it, nothing measured is
# missing from the estimate, and would_raise fires when query or resolve
# raises.
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


def _measure(csvpaths, reference):
    finder = ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=csvpaths)
    raised = None
    with ReadCounter.for_csvpaths(csvpaths) as query:
        try:
            selection = finder.query()
        except Exception as e:
            raised = e
    if raised is not None:
        return {QUERY: dict(query.reads), RESOLVE: {}}, raised
    with ReadCounter.for_csvpaths(csvpaths) as resolve:
        try:
            finder.resolve_from(selection)
        except Exception as e:
            raised = e
    return {QUERY: dict(query.reads), RESOLVE: dict(resolve.reads)}, raised


def _problems(est, measured, raised) -> list:
    problems = []
    for part in (QUERY, RESOLVE):
        predicted = {}
        for r in est.reads:
            if r.part == part:
                n, basis = predicted.get(r.kind, (0, EXACT))
                predicted[r.kind] = (n + r.count, UPPER_BOUND if UPPER_BOUND in (basis, r.basis) else r.basis)
        for kind, count in measured[part].items():
            if kind not in predicted:
                problems.append(f"{part} {kind}: measured {count}, not estimated")
        for kind, (count, basis) in predicted.items():
            real = measured[part].get(kind, 0)
            if basis == EXACT and count != real:
                problems.append(f"{part} {kind}: exact {count} but measured {real}")
            if basis == UPPER_BOUND and count < real:
                problems.append(f"{part} {kind}: upper bound {count} below measured {real}")
    if raised is not None and not est.would_raise:
        problems.append(f"resolve raised ({raised}) but would_raise is None")
    if raised is None and est.would_raise and not est.would_raise.startswith("may"):
        problems.append(f"would_raise ({est.would_raise}) but resolve did not raise")
    return problems


@pytest.mark.parametrize("reference", SHAPES)
def test_the_estimate_keeps_its_contract(csvpaths, reference):
    finder = ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=csvpaths)
    est = finder.estimate()
    measured, raised = _measure(csvpaths, reference)
    assert _problems(est, measured, raised) == []
