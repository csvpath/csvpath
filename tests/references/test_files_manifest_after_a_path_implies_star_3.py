#
# FILES ':manifest()' after a path, e.g. '$acme.files.orders/:manifest()',
# is the manifest records of the registrations directly under orders/ (a
# '*' is implied after the path). David, 2026-11-22, decision log D40 c, by
# extension of compendium 6.13b: a ':manifest()' that is not bare points to
# registration records. It read as 'orders:manifest()' -- the entries of a
# file home NAMED orders -- which is empty on a normal layout (D38).
#
import os

import pytest

from csvpath import CsvPaths
from csvpath.references.reference_finder_factory_3 import ReferenceFinderFactory3
from tests.references.cost.test_results_estimate_soundness_3 import (
    _measure,
    _problems,
)
from tests.references.test_files_wildcard_paths_3 import (  # noqa: F401
    _config_file,
    layout,
)


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


#
# any number of template levels (David, 2026-11-22, D40 j): the '/' before
# ':manifest()' implies one '*', after a '*' as after a directory, so
# '*/*/*/:manifest()' is '*/*/*/*:manifest()': the registrations of every
# template with three directories. It was '*/*/*:manifest()', one level
# short, while 'a/b/c/:manifest()' already reached a/b/c/.
#
DEEP = [
    ("", "zero.csv", 1),
    ("a", "one.csv", 1),
    ("a/b", "two.csv", 1),
    ("a/b/c", "three.csv", 2),
    ("x/y/z", "three.csv", 1),
    ("a/b/c/d", "four.csv", 1),
    ("a/b/c/d/e", "five.csv", 1),
]


@pytest.fixture(scope="module")
def deep(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("files_manifest_deep")
    previous = os.environ.get("CSVPATH_CONFIG_PATH")
    os.environ["CSVPATH_CONFIG_PATH"] = _config_file(tmp)
    try:
        p = CsvPaths()
        n = 0
        for dirs, filename, versions in DEEP:
            for v in range(versions):
                n += 1
                src = tmp / "src" / str(n)
                src.mkdir(parents=True)
                (src / filename).write_text(f"id,v\n{n},{v}\n", encoding="utf-8")
                p.file_manager.add_named_file(
                    name="alpha",
                    path=str(src / filename),
                    template=f"{dirs}/:filename" if dirs else None,
                )
        yield p
    finally:
        if previous is None:
            os.environ.pop("CSVPATH_CONFIG_PATH", None)
        else:
            os.environ["CSVPATH_CONFIG_PATH"] = previous


def _depth_of(file_home: str) -> int:
    """the number of template directories above a file home"""
    return file_home.split("/named_files/alpha/", 1)[1].count("/")


@pytest.mark.parametrize("levels", [1, 2, 3, 4, 5])
def test_every_template_depth(deep, levels):
    reference = "$alpha.files." + "*/" * levels + ":manifest()"
    rows, data = _rows_and_data(deep, reference)
    expected = [
        e["uuid"]
        for e in deep.file_manager.get_manifest("alpha")
        if _depth_of(e["file_home"]) == levels
    ]
    assert expected
    assert [uuid for _, uuid in rows] == expected
    assert [record["uuid"] for record in data] == expected
    explicit = "$alpha.files." + "*/" * levels + "*:manifest()"
    assert _rows_and_data(deep, explicit) == (rows, data)


def test_three_levels_spelled_out(deep):
    # the issue as David wrote it, with both templates of three directories
    rows, _ = _rows_and_data(deep, "$alpha.files.*/*/*/:manifest()")
    homes = [path for path, _ in rows]
    assert len(homes) == 3
    literal, _ = _rows_and_data(deep, "$alpha.files.a/b/c/:manifest()")
    mixed, _ = _rows_and_data(deep, "$alpha.files.a/*/c/:manifest()")
    assert len(literal) == 2 and mixed == literal
    assert set(uuid for _, uuid in literal) < set(uuid for _, uuid in rows)


def test_deeper_than_any_template_is_empty(deep):
    assert (
        _finder(p=deep, reference="$alpha.files." + "*/" * 6 + ":manifest()")
        .query()
        .results
        == []
    )


@pytest.mark.parametrize(
    "reference",
    [
        "$alpha.files.*/:manifest()",
        "$alpha.files.*/*/*/:manifest()",
        "$alpha.files.*/*/*/*/*/:manifest()",
        "$alpha.files.a/*/c/:manifest()",
        "$alpha.files.*/*/*/*/*/*/:manifest()",
    ],
)
def test_the_deep_estimate_keeps_its_contract(deep, reference):
    measured, raised = _measure(deep, reference)
    assert raised is None
    assert (
        _problems(_finder(p=deep, reference=reference).estimate(), measured, raised)
        == []
    )
