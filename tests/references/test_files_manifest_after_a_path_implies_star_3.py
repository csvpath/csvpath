#
# FILES ':manifest()' after a path, e.g. '$acme.files.orders/:manifest()',
# is the manifest records of the registrations directly under orders/ (a
# '*' is implied after the path). David, 2026-11-22, decision log D40 c, by
# extension of compendium 6.13b: a ':manifest()' that is not bare points to
# registration records. It read as 'orders:manifest()' -- the entries of a
# file home NAMED orders -- which is empty on a normal layout (D38).
#
import pytest

from csvpath.references.reference_finder_factory_3 import ReferenceFinderFactory3
from tests.references.cost.test_results_estimate_soundness_3 import (
    _measure,
    _problems,
)
from tests.references.test_files_wildcard_paths_3 import layout  # noqa: F401


def _finder(*, p, reference: str):
    return ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=p)


def _rows_and_data(p, reference: str) -> tuple:
    finder = _finder(p=p, reference=reference)
    selection = finder.query()
    return (
        [(str(r.path), r.uuid) for r in selection.results],
        [r.data for r in finder.resolve_each(selection).results],
    )


@pytest.mark.parametrize(
    "name,path",
    [
        ("beta", "APAC"),
        ("beta", "EMEA"),
        ("acme", "invoices/jan"),
        ("acme", "shipments/feb"),
    ],
)
def test_it_is_the_explicit_star_form(layout, name, path):  # noqa: F811
    p, _ = layout
    implied = _rows_and_data(p, f"${name}.files.{path}/:manifest()")
    explicit = _rows_and_data(p, f"${name}.files.{path}/*:manifest()")
    assert implied == explicit
    assert implied[0]


def test_the_records_are_the_registrations_under_the_path(layout):  # noqa: F811
    p, _ = layout
    rows, data = _rows_and_data(p, "$beta.files.APAC/:manifest()")
    expected = [
        e["uuid"]
        for e in p.file_manager.get_manifest("beta")
        if "/APAC/" in e["file_home"]
    ]
    assert [uuid for _, uuid in rows] == expected
    assert [record["uuid"] for record in data] == expected


def test_one_level_only(layout):  # noqa: F811
    # an implied '*' is one level: orders/2026/four.csv is not directly under orders/
    p, _ = layout
    assert (
        _finder(p=p, reference="$cappa.files.orders/:manifest()").query().results == []
    )


def test_a_path_with_nothing_under_it_is_empty(layout):  # noqa: F811
    p, _ = layout
    assert _finder(p=p, reference="$beta.files.LATAM/:manifest()").query().results == []


def test_a_bare_manifest_is_unchanged(layout):  # noqa: F811
    # the whole name_one ':manifest()' is still the manifest file
    p, _ = layout
    results = _finder(p=p, reference="$beta.files.:manifest()").query().results
    assert [str(r.path).rsplit("/", 1)[-1] for r in results] == ["manifest.json"]


@pytest.mark.parametrize(
    "reference",
    [
        "$beta.files.APAC/:manifest()",
        "$beta.files.EMEA/:manifest()",
        "$cappa.files.orders/:manifest()",
        "$beta.files.LATAM/:manifest()",
        "$acme.files.invoices/jan/:manifest()",
    ],
)
def test_the_estimate_keeps_its_contract(layout, reference):  # noqa: F811
    p, _ = layout
    measured, raised = _measure(p, reference)
    assert raised is None
    assert (
        _problems(_finder(p=p, reference=reference).estimate(), measured, raised) == []
    )
