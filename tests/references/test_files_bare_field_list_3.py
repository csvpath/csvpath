#
# the bare FILES ':fingerprint()' / ':uuid()' list (compendium 6.19: "The
# following two references both return a list of the registration
# fingerprints found in `acme`. `$acme.files.:fingerprint()`
# `$acme.files.:manifest():fingerprint()`"; 6.44 "Likewise"). It raised
# "field functions attached directly to name_one" (David, 2026-11-22,
# decision log D40 i). Under '*' or a pattern root the bare form is not
# specified, so it raises naming the ledger form (D41).
#
import pytest

from csvpath.references.reference_exceptions_3 import ReferenceException3
from csvpath.references.reference_finder_factory_3 import ReferenceFinderFactory3
from tests.references.cost.test_results_estimate_soundness_3 import (
    _measure,
    _problems,
)
from tests.references.test_files_wildcard_paths_3 import NAMES, layout  # noqa: F401

FIELDS = ["fingerprint", "uuid"]


def _finder(*, p, reference: str):
    return ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=p)


def _rows_and_data(p, reference: str) -> tuple:
    finder = _finder(p=p, reference=reference)
    selection = finder.query()
    rows = [(str(r.path), r.uuid) for r in selection.results]
    return rows, [r.data for r in finder.resolve_each(selection).results]


@pytest.mark.parametrize("field", FIELDS)
@pytest.mark.parametrize("name", NAMES)
def test_the_bare_form_is_the_manifest_form(layout, field, name):  # noqa: F811
    p, _ = layout
    bare = _rows_and_data(p, f"${name}.files.:{field}()")
    spelled = _rows_and_data(p, f"${name}.files.:manifest():{field}()")
    assert bare == spelled
    assert bare[0]


@pytest.mark.parametrize("field", FIELDS)
def test_the_values_are_the_manifest_field(layout, field):  # noqa: F811
    p, _ = layout
    _, data = _rows_and_data(p, f"$beta.files.:{field}()")
    assert data == [e[field] for e in p.file_manager.get_manifest("beta")]


@pytest.mark.parametrize("field", FIELDS)
@pytest.mark.parametrize("root", ["$*", "$:regex(/^b/)", '$:choice("beta")'])
def test_a_star_or_pattern_root_raises_naming_the_ledger_form(layout, field, root):  # noqa: F811
    p, _ = layout
    with pytest.raises(
        ReferenceException3, match=rf"\$\*\.files\.:manifest\(\):{field}\(\)"
    ):
        _finder(p=p, reference=f"{root}.files.:{field}()").query()


@pytest.mark.parametrize(
    "reference",
    ["$beta.files.:fingerprint().:last()", "$beta.files.:fingerprint()#sheet1"],
)
def test_a_combination_still_raises(layout, reference):  # noqa: F811
    p, _ = layout
    with pytest.raises(ReferenceException3):
        _finder(p=p, reference=reference).query()


def test_a_missing_named_file_is_empty(layout):  # noqa: F811
    p, _ = layout
    assert _finder(p=p, reference="$nope.files.:fingerprint()").query().results == []


def test_the_argued_form_is_unchanged(layout):  # noqa: F811
    p, _ = layout
    entry = p.file_manager.get_manifest("beta")[0]
    results = (
        _finder(p=p, reference=f'$beta.files.:fingerprint("{entry["fingerprint"]}")')
        .query()
        .results
    )
    assert [r.uuid for r in results] == [entry["uuid"]]


@pytest.mark.parametrize(
    "reference",
    [
        "$beta.files.:fingerprint()",
        "$beta.files.:uuid()",
        "$nope.files.:fingerprint()",
        "$*.files.:fingerprint()",
        "$:regex(/^b/).files.:uuid()",
        '$beta.files.:fingerprint("nope")',
        '$*.files.:uuid("nope")',
    ],
)
def test_the_estimate_keeps_its_contract(layout, reference):  # noqa: F811
    p, _ = layout
    measured, raised = _measure(p, reference)
    estimate = _finder(p=p, reference=reference).estimate()
    assert _problems(estimate, measured, raised) == []
    if raised is None:
        # the argued and the bare list forms are legal: no raise predicted
        assert not estimate.would_raise, estimate.would_raise
