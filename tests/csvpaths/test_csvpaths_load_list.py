"""load_list() in named-paths group runs: lists stored with the asset
manager's store_list() and read from the group's assets/<name>.txt."""

import json
import os

import pytest

from csvpath import CsvPaths
from csvpath.managers.paths.paths_asset_manager import PathsAssetManager
from csvpath.util.nos import Nos

GROUP = "load_list_test"
NAMED_FILE = "load_list_test_data"


@pytest.fixture
def paths(tmp_path):
    p = CsvPaths()
    p.paths_manager.remove_named_paths(GROUP)
    p.file_manager.remove_named_file(NAMED_FILE)
    data = tmp_path / "d.csv"
    data.write_text("id\na\nb\nc\nd\n", encoding="utf-8")
    p.file_manager.add_named_file(name=NAMED_FILE, path=str(data))
    yield p
    p.paths_manager.remove_named_paths(GROUP)
    p.file_manager.remove_named_file(NAMED_FILE)


def _group(paths: CsvPaths, body: str) -> None:
    paths.paths_manager.add_named_paths(
        name=GROUP, paths=[f"~ id: lists ~\n$[1*][ {body} ]"]
    )


def _run(paths: CsvPaths):
    paths.collect_paths(filename=NAMED_FILE, pathsname=GROUP)
    results = paths.results_manager.get_named_results(GROUP)
    assert len(results) == 1
    return results[0]


def test_store_list_writes_the_group_asset(paths) -> None:
    _group(paths, "yes()")
    am = paths.paths_manager.asset_manager
    p = am.store_list(name=GROUP, list_name="ids", values=["b", "d"])
    home = paths.paths_manager.named_paths_home(GROUP)
    assert p == Nos(Nos(home).join("assets")).join("ids.txt")
    with open(p, encoding="utf-8") as f:
        assert f.read() == "b\nd\n"
    assert am.list_path(name=GROUP, list_name="ids") == p


def test_list_path_creates_nothing(paths) -> None:
    _group(paths, "yes()")
    am = paths.paths_manager.asset_manager
    p = am.list_path(name=GROUP, list_name="ids")
    assert not Nos(os.path.dirname(p)).dir_exists()


@pytest.mark.parametrize("bad", ["", "ids.txt", ".ids", "a/b", "a b", None])
def test_store_list_bad_names(paths, bad) -> None:
    _group(paths, "yes()")
    with pytest.raises(ValueError):
        paths.paths_manager.asset_manager.store_list(
            name=GROUP, list_name=bad, values=[]
        )


def test_store_list_bad_values(paths) -> None:
    _group(paths, "yes()")
    am = paths.paths_manager.asset_manager
    with pytest.raises(ValueError):
        am.store_list(name=GROUP, list_name="ids", values=["a\nb"])
    with pytest.raises(TypeError):
        am.store_list(name=GROUP, list_name="ids", values=[1])
    with pytest.raises(TypeError):
        am.store_list(name=GROUP, list_name="ids", values="a")


def test_load_list_in_a_group_run(paths) -> None:
    _group(paths, '@ids.tmp = load_list("ids") in(#id, @ids)')
    paths.paths_manager.asset_manager.store_list(
        name=GROUP, list_name="ids", values=["b", "d"]
    )
    result = _run(paths)
    assert [line[0] for line in result.lines.to_list()] == ["b", "d"]
    #
    # tmp keeps the list out of vars.json
    #
    with open(Nos(result.instance_dir).join("vars.json"), encoding="utf-8") as f:
        assert "ids" not in json.load(f)


def test_load_list_without_tmp_is_in_vars_json(paths) -> None:
    _group(paths, '@ids = load_list("ids") in(#id, @ids)')
    paths.paths_manager.asset_manager.store_list(
        name=GROUP, list_name="ids", values=["b"]
    )
    result = _run(paths)
    with open(Nos(result.instance_dir).join("vars.json"), encoding="utf-8") as f:
        assert json.load(f)["ids"] == ["b"]


def test_load_list_missing_in_a_group_is_an_error(paths) -> None:
    _group(paths, 'in(#id, load_list("ids"))')
    with pytest.raises(Exception, match="Cannot load list 'ids'"):
        _run(paths)


def test_load_list_in_a_group_never_falls_back_to_a_path(paths, tmp_path) -> None:
    #
    # a .txt path that exists is still not used in a group run: the list
    # must be the group's
    #
    p = tmp_path / "ids.txt"
    p.write_text("b\n", encoding="utf-8")
    _group(paths, f'in(#id, load_list("{p}"))')
    with pytest.raises(Exception, match="Cannot load list"):
        _run(paths)


def test_list_suffix() -> None:
    assert PathsAssetManager.LIST_SUFFIX == ".txt"
