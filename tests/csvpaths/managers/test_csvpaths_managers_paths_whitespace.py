"""Whitespace around csvpaths in a named-paths group.

The group file separates csvpaths with "\\n\\n---- CSVPATH ----\\n\\n".
PathsManager.get_named_paths() returns each csvpath without that padding,
the same as the manifest's named_paths and _get_csvpaths_from_file().
Before, the padding came back with each csvpath, so every append re-wrapped
it and the newlines grew, and an out-of-band update to the group file put
the padded text into the manifest.
"""

import pytest

from csvpath import CsvPaths

NAME = "paths_whitespace_test"
MARKER = "---- CSVPATH ----"


@pytest.fixture
def paths():
    p = CsvPaths()
    p.paths_manager.remove_named_paths(NAME)
    yield p
    p.paths_manager.remove_named_paths(NAME)


def _group_file(paths: CsvPaths) -> str:
    manifest = paths.paths_manager.get_manifest_for_name(NAME)
    with open(manifest[-1]["group_file_path"], encoding="utf-8") as f:
        return f.read()


def _append_three(paths: CsvPaths) -> None:
    pm = paths.paths_manager
    pm.add_named_paths(name=NAME, paths=["$[*][ yes() ]"])
    for i in range(3):
        pm.add_named_paths(name=NAME, paths=[f"$[*][ no() {i} ]"], append=True)


EXPECTED = ["$[*][ yes() ]", "$[*][ no() 0 ]", "$[*][ no() 1 ]", "$[*][ no() 2 ]"]


def test_paths_whitespace_get_named_paths_is_stripped(paths) -> None:
    paths.paths_manager.add_named_paths(
        name=NAME, paths=["$[*][ yes() ]", "  $[*][ no() ]\n"]
    )
    assert paths.paths_manager.get_named_paths(NAME) == [
        "$[*][ yes() ]",
        "$[*][ no() ]",
    ]


def test_paths_whitespace_appends_do_not_grow_padding(paths) -> None:
    _append_three(paths)
    assert paths.paths_manager.get_named_paths(NAME) == EXPECTED
    expected = "".join(f"\n\n{MARKER}\n\n{p}" for p in EXPECTED)
    assert _group_file(paths) == expected


def test_paths_whitespace_appends_manifest_named_paths(paths) -> None:
    _append_three(paths)
    manifest = paths.paths_manager.get_manifest_for_name(NAME)
    assert len(manifest) == 4
    assert manifest[-1]["named_paths"] == EXPECTED


def test_paths_whitespace_out_of_band_edit_manifest_is_stripped(paths) -> None:
    paths.paths_manager.add_named_paths(name=NAME, paths=["$[*][ yes() ]"])
    manifest = paths.paths_manager.get_manifest_for_name(NAME)
    with open(manifest[-1]["group_file_path"], "a", encoding="utf-8") as f:
        f.write(f"\n\n{MARKER}\n\n  $[*][ no() ]  \n")
    assert paths.paths_manager.get_named_paths(NAME) == [
        "$[*][ yes() ]",
        "$[*][ no() ]",
    ]
    manifest = paths.paths_manager.get_manifest_for_name(NAME)
    assert len(manifest) == 2
    assert manifest[-1]["named_paths"] == ["$[*][ yes() ]", "$[*][ no() ]"]


def test_paths_whitespace_read_does_not_change_fingerprint(paths) -> None:
    _append_three(paths)
    before = _group_file(paths)
    paths.paths_manager.get_named_paths(NAME)
    paths.paths_manager.get_named_paths(NAME)
    assert _group_file(paths) == before
    assert len(paths.paths_manager.get_manifest_for_name(NAME)) == 4
