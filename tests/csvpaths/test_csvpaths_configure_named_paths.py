"""PathsManager.configure_named_paths(): a named-paths group created
without a load, as FileManager.configure_named_file creates a named-file
without a registration. Pins what an empty group does, and that reading one
writes nothing."""

import os

import pytest

from csvpath import CsvPaths
from csvpath.util.exceptions import InputException
from csvpath.util.nos import Nos

GROUP = "configure_test_group"
NAMED_FILE = "configure_test_data"


@pytest.fixture
def paths(tmp_path):
    p = CsvPaths()
    p.paths_manager.remove_named_paths(GROUP)
    p.file_manager.remove_named_file(NAMED_FILE)
    data = tmp_path / "d.csv"
    data.write_text("id\na\nb\n", encoding="utf-8")
    p.file_manager.add_named_file(name=NAMED_FILE, path=str(data))
    yield p
    p.paths_manager.remove_named_paths(GROUP)
    p.file_manager.remove_named_file(NAMED_FILE)


def _files(paths: CsvPaths) -> list[str]:
    home = paths.paths_manager.named_paths_home(GROUP, assure=False)
    return sorted(os.listdir(home))


def test_configure_creates_an_empty_group(paths) -> None:
    pm = paths.paths_manager
    home = pm.configure_named_paths(GROUP)
    assert home == pm.named_paths_home(GROUP, assure=False)
    assert _files(paths) == ["README.md", "definition.json"]
    assert pm.has_named_paths(GROUP)
    assert GROUP in pm.named_paths_names
    assert pm.get_json_paths_file(GROUP) == {GROUP: []}


def test_empty_group_reads(paths) -> None:
    pm = paths.paths_manager
    pm.configure_named_paths(GROUP)
    assert pm.get_named_paths(GROUP) == []
    assert pm.number_of_named_paths(GROUP) == 0
    assert pm.get_manifest_for_name(GROUP) == []


def test_reading_an_empty_group_writes_nothing(paths) -> None:
    #
    # no manifest.json, no group.csvpaths: reads are reads
    #
    pm = paths.paths_manager
    pm.configure_named_paths(GROUP)
    before = _files(paths)
    pm.get_named_paths(GROUP)
    pm.number_of_named_paths(GROUP)
    pm.get_manifest_for_name(GROUP)
    assert _files(paths) == before


def test_running_an_empty_group_fails_clearly(paths) -> None:
    paths.paths_manager.configure_named_paths(GROUP)
    with pytest.raises(InputException, match="is empty"):
        paths.collect_paths(filename=NAMED_FILE, pathsname=GROUP)


def test_assets_can_be_stored_before_the_first_load(paths) -> None:
    pm = paths.paths_manager
    pm.configure_named_paths(GROUP)
    p = pm.asset_manager.store_list(name=GROUP, list_name="ids", values=["b"])
    assert Nos(p).exists()


@pytest.mark.parametrize("append", [False, True])
def test_first_load_after_configure(paths, append: bool) -> None:
    pm = paths.paths_manager
    pm.configure_named_paths(GROUP)
    pm.asset_manager.store_list(name=GROUP, list_name="ids", values=["b"])
    pm.add_named_paths(
        name=GROUP,
        paths=['~ id: one ~ $[1*][ in(#id, load_list("ids")) ]'],
        append=append,
    )
    assert pm.get_named_paths(GROUP) == [
        '~ id: one ~ $[1*][ in(#id, load_list("ids")) ]'
    ]
    #
    # one version: the first load, not an append to something
    #
    assert len(pm.get_manifest_for_name(GROUP)) == 1
    paths.collect_paths(filename=NAMED_FILE, pathsname=GROUP)
    result = paths.results_manager.get_named_results(GROUP)[0]
    assert [line[0] for line in result.lines.to_list()] == ["b"]


def test_configure_leaves_an_existing_group_as_it_is(paths) -> None:
    pm = paths.paths_manager
    pm.add_named_paths(name=GROUP, paths=["~ id: one ~ $[1*][ yes() ]"])
    pm.describer.store_json(GROUP, {GROUP: ["kept"]})
    manifest = pm.get_manifest_for_name(GROUP)
    pm.configure_named_paths(GROUP)
    assert pm.get_named_paths(GROUP) == ["~ id: one ~ $[1*][ yes() ]"]
    assert pm.get_json_paths_file(GROUP) == {GROUP: ["kept"]}
    assert pm.get_manifest_for_name(GROUP) == manifest


def test_configure_twice_is_harmless(paths) -> None:
    pm = paths.paths_manager
    pm.configure_named_paths(GROUP)
    pm.configure_named_paths(GROUP)
    assert _files(paths) == ["README.md", "definition.json"]


@pytest.mark.parametrize("bad", ["", "  ", None, "$group", "a.b"])
def test_configure_bad_names(paths, bad) -> None:
    with pytest.raises(ValueError):
        paths.paths_manager.configure_named_paths(bad)


def test_remove_an_empty_group(paths) -> None:
    pm = paths.paths_manager
    pm.configure_named_paths(GROUP)
    pm.remove_named_paths(GROUP)
    assert not pm.has_named_paths(GROUP)
