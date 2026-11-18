import random

import pytest

from csvpath.references.reference_finder_factory_3 import ReferenceFinderFactory3
from tests.references.cost.test_results_estimate_soundness_3 import (  # noqa: F401
    _measure,
    _problems,
    csvpaths,
)

#
# A seeded sweep of generated FILES and CSVPATHS references: the shape lists
# pin the families reviewers named, and this keeps the contract over their
# combinations (two name_one functions, a name_three, pattern roots). The
# references that fail to parse are skipped; the rest are held to the same
# contract as the listed shapes.
#
PARTS = {
    "files": {
        "roots": [
            "orders",
            "acme_invoices",
            "zipcodes",
            "*",
            ":regex(/^o/)",
            ":regex(/^(orders|zipcodes)$/)",
        ],
        "ones": [
            ":flatten()",
            ":manifest()",
            ":definition()",
            ":all()",
            ":last()",
            ":first()",
            ':type("csv")',
            ':status("failed")',
            ':lifecycle("active")',
            ":template()",
            ":sources()",
            ":name(/food/)",
            ":uuid()",
            ":today()",
            ':after("2020-01-01")',
            ":from(0):to(1)",
            ":index(0)",
        ],
        "threes": [
            "",
            ".:last()",
            ".:first()",
            ".:all()",
            ".0",
            ".1-3",
            ".:uuid()",
            '.:type("csv")',
            ".:last():uuid()",
            ".:from(0)",
            ".:today()",
            ".:last():sources()",
        ],
    },
    "csvpaths": {
        "roots": [
            "validate_orders",
            "scan_invoices",
            "*",
            ":regex(/^v/)",
            ":regex(/^(validate|scan)/)",
        ],
        "ones": [
            ":manifest()",
            ":definition()",
            ":all()",
            ":last()",
            ":first()",
            ":index(1)",
            ':having("candy check")',
            ':status("unchanged")',
            ':lifecycle("active")',
            ":template()",
            ":scripts()",
            ":uuid()",
            ':after("2020-01-01")',
            ":from(0):to(1)",
            ":named_paths_name()",
        ],
        "threes": ["", ".0", ".1", ".0-1", ".:from(0)", ".:to(1)", ".company_names"],
    },
}
PER_DATATYPE = 300


def _references(datatype: str) -> list:
    parts = PARTS[datatype]
    rng = random.Random(20261118)
    references = []
    while len(references) < PER_DATATYPE:
        one = rng.choice(parts["ones"]) + (
            rng.choice(parts["ones"]) if rng.random() < 0.4 else ""
        )
        reference = f"${rng.choice(parts['roots'])}.{datatype}.{one}{rng.choice(parts['threes'])}"
        if reference not in references:
            references.append(reference)
    return references


@pytest.mark.parametrize("reference", _references("files") + _references("csvpaths"))
def test_a_generated_reference_keeps_the_contract(csvpaths, reference):  # noqa: F811
    try:
        finder = ReferenceFinderFactory3.for_reference(
            reference=reference, csvpaths=csvpaths
        )
    except Exception:
        pytest.skip("does not parse")
    estimate = finder.estimate()
    measured, raised = _measure(csvpaths, reference)
    assert _problems(estimate, measured, raised) == []
