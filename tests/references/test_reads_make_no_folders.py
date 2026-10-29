"""Resolving a v3 reference never writes to the named-files, named-paths or
archive roots, even when the reference names a group that does not exist
or was deleted.

Before this fix, a CSVPATHS reference to a missing or deleted group made
its folder (PathsManager.named_paths_home creates one) and, with the cache
on, a manifest.json holding [] (CacheIntermediary.get_json writes one on a
miss). The group then showed up in paths_names, and a deleted group came
back as an empty folder. Shadow mode found it: the filesystem listed
groups that SQL, correctly, did not.

FILES and RESULTS did not have the problem; they are here so they stay
that way.
"""

import json
import os

import pytest

from csvpath import CsvPaths
from csvpath.references.reference_finder_factory_3 import ReferenceFinderFactory3
from csvpath.references.sources.filesystem_reference_source import (
    FilesystemReferenceSource,
)

SHAPES = {
    "files": [
        ":all()",
        ":first()",
        ":last()",
        ":groups()",
        ":flatten()",
        ":manifest()",
        ":definition()",
        ":readme()",
        ":named_file_home()",
        ":last():named_file_home()",
        ":last():manifest()",
    ],
    "csvpaths": [
        ":all()",
        ":first()",
        ":last()",
        ":manifest()",
        ":definition()",
        ":readme()",
        ":named_paths_home()",
        ":last():named_paths_home()",
        ":last():manifest()",
        ":last():named_paths_count()",
    ],
    "results": [
        ":all()",
        ":last()",
        ":flatten()",
        ":manifest()",
        ":last().:all()",
        ":last():manifest()",
        ":last().:errors()",
    ],
}
#
# per datatype: a name that never existed, and one that was deleted
#
MISSING = {
    "files": ["nope", "fgone"],
    "csvpaths": ["nope", "pgone"],
    "results": ["nope", "rgone"],
}
REFERENCES = [
    f"${name}.{datatype}.{shape}"
    for datatype, shapes in SHAPES.items()
    for name in MISSING[datatype]
    for shape in shapes
]


def _paths(tmp_path, *, use_cache: str) -> CsvPaths:
    p = CsvPaths()
    c = p.config
    c.add_to_config(section="inputs", key="files", value=str(tmp_path / "nf"))
    c.add_to_config(section="inputs", key="csvpaths", value=str(tmp_path / "np"))
    c.add_to_config(section="results", key="archive", value=str(tmp_path / "ar"))
    c.add_to_config(section="listeners", key="groups", value="default")
    c.add_to_config(section="cache", key="use_cache", value=use_cache)
    return p


def _build(p: CsvPaths, tmp_path) -> None:
    for name in ["orders", "fgone"]:
        data = tmp_path / f"{name}.csv"
        data.write_text("id,amount\n1,10\n", encoding="utf-8")
        p.file_manager.add_named_file(name=name, path=str(data))
    for name in ["acme", "pgone", "rgone"]:
        f = tmp_path / f"{name}.csvpaths"
        f.write_text("~ id: first ~ $[*][yes()]", encoding="utf-8")
        p.paths_manager.add_named_paths_from_file(name=name, file_path=str(f))
    p.collect_paths(filename="orders", pathsname="acme")
    p.collect_paths(filename="orders", pathsname="rgone")
    p.file_manager.remove_named_file("fgone")
    p.paths_manager.remove_named_paths("pgone")
    p.results_manager.remove_named_results("rgone")


def _tree(p: CsvPaths) -> set:
    c = p.config
    out = set()
    for root in [
        c.get(section="inputs", name="files"),
        c.get(section="inputs", name="csvpaths"),
        c.get(section="results", name="archive"),
    ]:
        for d, _, files in os.walk(root):
            out.add(d)
            for f in files:
                out.add(os.path.join(d, f))
    return out


def _resolve(p: CsvPaths, reference: str):
    try:
        finder = ReferenceFinderFactory3.for_reference(reference=reference, csvpaths=p)
        return ("ok", finder.query())
    except Exception as ex:
        return ("raised", type(ex))


@pytest.fixture(scope="module", params=["yes", "no"], ids=["cache", "no_cache"])
def built(request, tmp_path_factory):
    tmp = tmp_path_factory.mktemp(f"no_folders_{request.param}")
    p = _paths(tmp, use_cache=request.param)
    _build(p, tmp)
    return p


# ===================
# references
# ===================


def test_the_deleted_names_are_gone(built):
    assert "fgone" not in built.file_manager.named_file_names
    assert "pgone" not in built.paths_manager.named_paths_names
    assert not os.path.exists(
        os.path.join(built.config.get(section="results", name="archive"), "rgone")
    )


@pytest.mark.parametrize("reference", REFERENCES)
def test_a_reference_to_a_missing_name_writes_nothing(built, reference):
    before = _tree(built)
    _resolve(built, reference)
    assert sorted(_tree(built) - before) == []


@pytest.mark.parametrize("reference", REFERENCES)
def test_a_reference_to_a_missing_name_finds_nothing(built, reference):
    #
    # the bare file pointers (:manifest(), :definition(), :readme()) give
    # a path that does not exist, as before; everything else gives none
    #
    kind, value = _resolve(built, reference)
    if kind == "raised":
        return
    for result in value:
        assert not os.path.exists(result.path), reference


def test_missing_groups_stay_out_of_the_names(built):
    for reference in REFERENCES:
        _resolve(built, reference)
    assert sorted(built.paths_manager.named_paths_names) == ["acme", "rgone"]
    assert FilesystemReferenceSource(csvpaths=built).paths_names() == [
        "acme",
        "rgone",
    ]


def test_an_existing_group_reads_as_before(built):
    kind, value = _resolve(built, "$acme.csvpaths.:all()")
    assert kind == "ok"
    assert len(value) == 1
    kind, value = _resolve(built, "$acme.csvpaths.:manifest()")
    assert os.path.exists(value.results[0].path)


# ===================
# PathsManager.named_paths_home
# ===================


@pytest.fixture
def paths(tmp_path):
    return _paths(tmp_path, use_cache="yes")


def test_named_paths_home_still_creates_by_default(paths):
    home = paths.paths_manager.named_paths_home("newgroup")
    assert os.path.isdir(home)


def test_named_paths_home_without_assure_creates_nothing(paths):
    home = paths.paths_manager.named_paths_home("newgroup", assure=False)
    assert not os.path.exists(home)
    assert home == paths.paths_manager.named_paths_home("newgroup")


def test_named_paths_home_without_assure_resolves_a_reference(paths):
    home = paths.paths_manager.named_paths_home("$newgroup.csvpaths.first", assure=False)
    assert home.endswith("newgroup")
    assert not os.path.exists(home)


@pytest.mark.parametrize("bad", [None, "no", 0, 1])
def test_named_paths_home_checks_assure(paths, bad):
    with pytest.raises(TypeError):
        paths.paths_manager.named_paths_home("newgroup", assure=bad)


def test_named_paths_home_checks_the_name(paths):
    with pytest.raises(ValueError):
        paths.paths_manager.named_paths_home(None, assure=False)


# ===================
# FilesystemReferenceSource.paths_manifest
# ===================


def test_paths_manifest_of_a_missing_group_is_empty_and_writes_nothing(paths):
    source = FilesystemReferenceSource(csvpaths=paths)
    before = _tree(paths)
    assert source.paths_manifest("newgroup") == []
    assert _tree(paths) == before


def test_paths_manifest_of_a_group_is_its_manifest(paths, tmp_path):
    f = tmp_path / "acme.csvpaths"
    f.write_text("~ id: first ~ $[*][yes()]", encoding="utf-8")
    paths.paths_manager.add_named_paths_from_file(name="acme", file_path=str(f))
    source = FilesystemReferenceSource(csvpaths=paths)
    assert source.paths_manifest("acme") == (
        paths.paths_manager.get_manifest_for_name("acme")
    )
    assert len(source.paths_manifest("acme")) == 1


def test_the_named_paths_home_field_creates_nothing(paths):
    #
    # :named_paths_home() is computed from the reference, never read. a
    # missing group returns no versions before the field is computed, so
    # call the computation directly
    #
    finder = ReferenceFinderFactory3.for_reference(
        reference="$newgroup.csvpaths.:last():named_paths_home()", csvpaths=paths
    )
    home = finder._compute_field("named_paths_home", finder.ref.parsed)
    assert home == paths.paths_manager.named_paths_home("newgroup", assure=False)
    assert not os.path.exists(home)


# ===================
# PathsManager.get_manifest_for_name
# ===================


def test_get_manifest_for_name_of_a_missing_group_is_empty_and_writes_nothing(paths):
    before = _tree(paths)
    assert paths.paths_manager.get_manifest_for_name("newgroup") == []
    assert paths.paths_manager.get_manifest_for_name("$newgroup.csvpaths.first") == []
    assert _tree(paths) == before


def test_get_manifest_for_name_of_a_deleted_group_is_empty_and_writes_nothing(
    paths, tmp_path
):
    f = tmp_path / "acme.csvpaths"
    f.write_text("~ id: first ~ $[*][yes()]", encoding="utf-8")
    paths.paths_manager.add_named_paths_from_file(name="acme", file_path=str(f))
    paths.paths_manager.remove_named_paths("acme")
    before = _tree(paths)
    assert paths.paths_manager.get_manifest_for_name("acme") == []
    assert _tree(paths) == before
    assert "acme" not in paths.paths_manager.named_paths_names


def test_get_manifest_for_name_of_a_group_reads_its_manifest(paths, tmp_path):
    f = tmp_path / "acme.csvpaths"
    f.write_text("~ id: first ~ $[*][yes()]", encoding="utf-8")
    paths.paths_manager.add_named_paths_from_file(name="acme", file_path=str(f))
    home = paths.paths_manager.named_paths_home("acme", assure=False)
    with open(os.path.join(home, "manifest.json"), encoding="utf-8") as file:
        on_disk = json.load(file)
    assert paths.paths_manager.get_manifest_for_name("acme") == on_disk
    assert len(on_disk) == 1
