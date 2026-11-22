#
# FILES ':manifest()' after a path with a pointer, range or filter, e.g.
# '$beta.files.APAC/*:manifest():first()'. Compendium 6.13b: a ':manifest()'
# in name_one "with a pointer, filter or range, and no field after it,
# resolves to the selected ... record(s)". The bare
# '$beta.files.:manifest():first()' did; after a path it raised "does not
# support functions attached directly to name_one" (logged reviewing #803;
# David, 2026-11-22: fix before release).
#
# Each pointer picks what the same pointer in name_three picks
# ('APAC/*.:first()'): '*' pools one level, ':all()'/':groups()' pick in
# each group (4.2). The result is the record, with the named-file's
# manifest.json as its path (5.7), as for 'APAC/*:manifest()'.
#
import pytest

from csvpath.references.reference_exceptions_3 import ReferenceException3
from csvpath.references.reference_finder_factory_3 import ReferenceFinderFactory3
from tests.references.cost.test_results_estimate_soundness_3 import (
    _measure,
    _problems,
)
from tests.references.test_files_wildcard_paths_3 import layout  # noqa: F401


def _finder(*, p, reference: str):
    return ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=p)


def _query_uuids(p, reference: str) -> list:
    return [r.uuid for r in _finder(p=p, reference=reference).query().results]


def _records(p, reference: str) -> list:
    finder = _finder(p=p, reference=reference)
    return [r.data for r in finder.resolve_each(finder.query()).results]


def _entries(p, *, name: str, under: str) -> list:
    """the named-file's own manifest entries whose file home is directly
    under `under`, in arrival order"""
    return [
        e
        for e in p.file_manager.get_manifest(name)
        if e["file_home"].split(f"/named_files/{name}/", 1)[1].rsplit("/", 1)[0]
        == under
    ]


#
# the pointer picks what the name_three pointer picks
#
SAME_VERSION = [
    ("$beta.files.APAC/*:manifest():first()", "$beta.files.APAC/*.:first()"),
    ("$beta.files.APAC/*:manifest():last()", "$beta.files.APAC/*.:last()"),
    ("$beta.files.APAC/*:manifest():index(1)", "$beta.files.APAC/*.:index(1)"),
    # the pointer may come first, as for the bare chain
    ("$beta.files.APAC/*:first():manifest()", "$beta.files.APAC/*.:first()"),
    # the '*' implied after the '/' (D40 c, j)
    ("$beta.files.APAC/:manifest():last()", "$beta.files.APAC/*.:last()"),
    ("$beta.files.*/:manifest():last()", "$beta.files.*/*.:last()"),
    (
        "$acme.files.invoices/jan/:manifest():first()",
        "$acme.files.invoices/jan/*.:first()",
    ),
    # a selector segment
    (
        '$beta.files.:name("APAC")/*:manifest():last()',
        '$beta.files.:name("APAC")/*.:last()',
    ),
    (
        '$cappa.files.:name("three.csv"):manifest():last()',
        '$cappa.files.:name("three.csv").:last()',
    ),
    # any depth, pooled (4.5)
    ("$acme.files.:flatten():manifest():last()", "$acme.files.:flatten().:last()"),
    (
        "$acme.files.shipments/:flatten():manifest():first()",
        "$acme.files.shipments/:flatten().:first()",
    ),
    (
        '$acme.files.:flatten()/:name("week1.csv"):manifest():last()',
        '$acme.files.:flatten()/:name("week1.csv").:last()',
    ),
    # a pointer in each group (4.2)
    ("$beta.files.APAC/:all():manifest():last()", "$beta.files.APAC/:all().:last()"),
    ("$beta.files.:groups():manifest():first()", "$beta.files.:groups().:first()"),
    (
        "$acme.files.shipments/:all()/*:manifest():last()",
        "$acme.files.shipments/:all()/*.:last()",
    ),
]


@pytest.mark.parametrize("reference,same_as", SAME_VERSION)
def test_the_pointer_picks_what_the_name_three_pointer_picks(
    layout,  # noqa: F811
    reference,
    same_as,
):
    p, _ = layout
    expected = _query_uuids(p, same_as)
    assert expected
    assert _query_uuids(p, reference) == expected
    assert [record["uuid"] for record in _records(p, reference)] == expected


def test_the_result_is_the_record_in_the_named_files_manifest(layout):  # noqa: F811
    p, _ = layout
    finder = _finder(p=p, reference="$beta.files.APAC/*:manifest():last()")
    results = finder.query().results
    assert len(results) == 1
    assert str(results[0].path).endswith("/beta/manifest.json")
    last = _entries(p, name="beta", under="APAC")[-1]
    assert finder.resolve_each(finder.query()).results[0].data == last


def test_the_first_of_the_pool_not_of_each_file_home(layout):  # noqa: F811
    # '*' pools: one record for APAC/, two.csv's first, not five.csv's too
    p, _ = layout
    first = _entries(p, name="beta", under="APAC")[0]
    assert _query_uuids(p, "$beta.files.APAC/*:manifest():first()") == [first["uuid"]]


#
# ranges and windows
#
def test_a_range_counts_in_the_pool(layout):  # noqa: F811
    p, _ = layout
    expected = [e["uuid"] for e in _entries(p, name="beta", under="APAC")][1:]
    assert _query_uuids(p, "$beta.files.APAC/*:manifest():from(1)") == expected


def test_a_window_reads_each_records_time(layout):  # noqa: F811
    # the layout is registered as the test runs
    p, _ = layout
    every = [e["uuid"] for e in _entries(p, name="beta", under="APAC")]
    assert _query_uuids(p, "$beta.files.APAC/*:manifest():today()") == every
    assert _query_uuids(p, "$beta.files.APAC/*:manifest():yesterday()") == []


#
# filters
#
@pytest.mark.parametrize(
    "reference,count",
    [
        ('$beta.files.APAC/*:manifest():type("csv")', 3),
        ('$beta.files.APAC/*:manifest():type("xlsx")', 0),
        # the gate filters before the pointer picks, in either order (6.28)
        ('$beta.files.APAC/*:manifest():last():type("csv")', 1),
        ('$beta.files.APAC/*:manifest():type("xlsx"):last()', 0),
    ],
)
def test_a_gate_filters(layout, reference, count):  # noqa: F811
    p, _ = layout
    assert len(_query_uuids(p, reference)) == count


def test_nothing_under_the_path_is_empty(layout):  # noqa: F811
    p, _ = layout
    assert _query_uuids(p, "$beta.files.LATAM/:manifest():first()") == []


#
# what still raises
#
def test_a_field_after_it_goes_in_name_three(layout):  # noqa: F811
    # 6.13b: "no field after it"; in FILES name_one picks the file and
    # name_three reads its fields (E2). The message gives the dotted form,
    # and the dotted form works.
    p, _ = layout
    with pytest.raises(ReferenceException3, match=r"after a '\.'") as e:
        _finder(p=p, reference="$beta.files.APAC/*:manifest():last():time()").query()
    suggested = str(e.value).rsplit("'", 2)[1]
    assert suggested == "APAC/*.:manifest():last():time()"
    values = [
        r.data
        for r in _finder(p=p, reference=f"$beta.files.{suggested}").resolve().results
    ]
    assert len(values) == 1 and isinstance(values[0], str)


def test_two_pointers_raise(layout):  # noqa: F811
    p, _ = layout
    with pytest.raises(ReferenceException3, match="at most one pointer"):
        _finder(p=p, reference="$beta.files.APAC/*:manifest():first():last()").query()


def test_a_worksheet_raises(layout):  # noqa: F811
    # a worksheet means sheet content; the chain resolves to records
    p, _ = layout
    with pytest.raises(ReferenceException3, match="worksheet"):
        _finder(p=p, reference="$beta.files.APAC/*#s:manifest():first()").query()


@pytest.mark.parametrize(
    "reference",
    [
        "$*.files.APAC/*:manifest():last()",
        "$:regex(/^b/).files.APAC/*:manifest():first()",
    ],
)
def test_a_traversal_root_still_raises(layout, reference):  # noqa: F811
    # not in this change: under '*', ':regex()' or ':choice()' a path with
    # ':manifest()' raises with or without a pointer, as on main (logged in
    # deferred_work_bucket_list.md)
    p, _ = layout
    with pytest.raises(ReferenceException3, match="traversal"):
        _finder(p=p, reference=reference).query()


#
# the estimate keeps its contract
#
@pytest.mark.parametrize(
    "reference",
    [reference for reference, _ in SAME_VERSION]
    + [
        "$beta.files.APAC/*:manifest():from(1)",
        "$beta.files.APAC/*:manifest():today()",
        "$beta.files.APAC/*:manifest():yesterday()",
        '$beta.files.APAC/*:manifest():type("csv")',
        '$beta.files.APAC/*:manifest():last():type("csv")',
        "$beta.files.LATAM/:manifest():first()",
    ],
)
def test_the_estimate_keeps_its_contract(layout, reference):  # noqa: F811
    p, _ = layout
    measured, raised = _measure(p, reference)
    assert raised is None
    assert (
        _problems(_finder(p=p, reference=reference).estimate(), measured, raised) == []
    )


@pytest.mark.parametrize(
    "reference",
    [
        "$beta.files.APAC/*:manifest():last():time()",
        "$beta.files.APAC/*:manifest():first():last()",
    ],
)
def test_the_estimate_of_a_raise_keeps_its_contract(layout, reference):  # noqa: F811
    p, _ = layout
    measured, raised = _measure(p, reference)
    assert raised is not None
    assert (
        _problems(_finder(p=p, reference=reference).estimate(), measured, raised) == []
    )
