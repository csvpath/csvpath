import pytest

from csvpath.references.reference_finder_factory_3 import ReferenceFinderFactory3
from tests.references.cost.csvpaths_shapes import SHAPES
from tests.references.cost.test_results_estimate_soundness_3 import (  # noqa: F401
    _measure,
    _problems,
    csvpaths,
)

#
# the CSVPATHS estimate's contract, the same as RESULTS': a count marked exact
# is the measured count, an upper bound is never below it, nothing measured
# is missing, and would_raise fires when query or resolve raises
#


@pytest.mark.parametrize("reference", SHAPES)
def test_the_csvpaths_estimate_keeps_its_contract(csvpaths, reference):  # noqa: F811
    finder = ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=csvpaths)
    est = finder.estimate()
    measured, raised = _measure(csvpaths, reference)
    assert _problems(est, measured, raised) == []


def test_the_csvpaths_estimate_reads_only_the_ledger(csvpaths):  # noqa: F811
    from tests.references.cost.read_counter import ReadCounter

    finder = ReferenceFinderFactory3.for_reference(
        reference='$*.csvpaths.:all():fingerprint()', csvpaths=csvpaths
    )
    with ReadCounter.for_csvpaths(csvpaths) as counter:
        finder.estimate()
    assert dict(counter.reads) == {"ledger": 1}
