"""The allowlist guard on tests/conftest.py's session wipe.

The wipe removes every local folder the active config names. These tests
check that it only ever removes folders under WIPE_ALLOWED in the repo root,
and that one refused path means nothing is removed. Only the
test_one_refused_path_removes_nothing tests remove anything, and only in
pytest's temp directory.
"""

import os

import pytest

from tests import conftest as cout

ROOT = cout.REPO_ROOT

#
# the local paths the configs used by the repo and CI name today, as the
# config reads them. see config/config.ini, assets/config/config.ini and
# assets/config/jenkins-local-*.ini
#
CURRENT = [
    "cache",
    "archive",
    "logs",
    "parquet",
    "tmp/local/archive",
    "tmp/transfers",
    "tmp/local/transfers",
    "tmp/local/inputs/named_files",
    "tmp/local/inputs/named_paths",
]
REMOTE = [
    "s3://csvpath-example-1/mac/inputs/named_files",
    "azure://csvpath/mac/inputs/named_files",
    "gs://csvpath-testing-1/mac/inputs/named_files",
    "sftp://server:22/mac/inputs/named_files",
]
CORPUS = [
    "tests/corpus/data/cache",
    "tests/corpus/data/archive",
    "tests/corpus/data/transfers",
    "tests/corpus/data/inputs/named_files",
    "tests/corpus/data/inputs/named_paths",
    "tests/corpus/data/logs",
]


@pytest.fixture
def at_root(monkeypatch):
    #
    # the configs paths are relative, and resolve against the working
    # directory, as pytest runs from the repo root
    #
    monkeypatch.chdir(ROOT)


def _check(paths, root=ROOT):
    return cout._check_wipe_paths(paths=paths, root=root, config_path="x.ini")


# ===================
# allowed
# ===================


def test_the_allowlist():
    assert cout.WIPE_ALLOWED == ["tmp", "cache", "archive", "logs", "parquet"]


def test_the_repo_root_is_the_repo_root():
    assert os.path.isfile(os.path.join(ROOT, "pyproject.toml"))
    assert os.path.isfile(os.path.join(ROOT, "tests", "conftest.py"))


@pytest.mark.parametrize("path", CURRENT)
def test_the_current_config_paths_are_allowed(at_root, path):
    assert _check([path]) == [path]


def test_absolute_paths_under_an_allowed_folder_are_allowed():
    p = os.path.join(ROOT, "tmp", "local", "archive")
    assert _check([p]) == [p]


def test_all_current_paths_are_returned_in_order(at_root):
    assert _check(CURRENT) == CURRENT


@pytest.mark.parametrize("path", REMOTE)
def test_remote_paths_are_dropped_not_refused(at_root, path):
    assert _check([path]) == []


@pytest.mark.parametrize("path", [None, ""])
def test_empty_paths_are_dropped(at_root, path):
    assert _check([path, "tmp/x"]) == ["tmp/x"]


# ===================
# refused
# ===================


@pytest.mark.parametrize("path", CORPUS)
def test_the_corpus_paths_are_refused(at_root, path):
    with pytest.raises(ValueError, match="Refusing to wipe"):
        _check([path])


@pytest.mark.parametrize(
    "path",
    [
        "/Users/someone/data/named_files",
        os.path.dirname(ROOT),
        ".",
        ROOT,
        "tests",
        "csvpath",
        "assets",
        "tmpfoo",
        "cache_old",
        "tmp/../tests/corpus/data",
        "tmp/../../elsewhere",
    ],
)
def test_paths_outside_the_allowlist_are_refused(at_root, path):
    with pytest.raises(ValueError, match="Refusing to wipe"):
        _check([path])


def test_the_error_names_every_refused_path_and_the_config(at_root):
    with pytest.raises(ValueError) as ex:
        cout._check_wipe_paths(
            paths=["tmp/ok", "tests/corpus/data/archive", "/elsewhere"],
            root=ROOT,
            config_path="tests/corpus/config/config.ini",
        )
    m = str(ex.value)
    assert "tests/corpus/config/config.ini" in m
    assert "tests/corpus/data/archive" in m
    assert "/elsewhere" in m
    assert "tmp/ok" not in m
    assert "Nothing was removed" in m


def test_relative_paths_resolve_against_the_working_directory(monkeypatch, tmp_path):
    #
    # outside the repo root, "tmp" is some other folder
    #
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match="Refusing to wipe"):
        _check(["tmp/local/archive"])


def test_a_symlink_out_of_an_allowed_folder_is_refused(tmp_path):
    root = tmp_path / "repo"
    (root / "tmp").mkdir(parents=True)
    keep = tmp_path / "keep"
    keep.mkdir()
    (root / "tmp" / "link").symlink_to(keep)
    with pytest.raises(ValueError, match="Refusing to wipe"):
        _check([str(root / "tmp" / "link")], root=str(root))


def test_a_symlinked_root_still_allows_its_folders(tmp_path):
    real = tmp_path / "real"
    (real / "tmp" / "a").mkdir(parents=True)
    link = tmp_path / "link"
    link.symlink_to(real)
    p = str(link / "tmp" / "a")
    assert _check([p], root=str(link)) == [p]


# ===================
# arguments
# ===================


@pytest.mark.parametrize("bad", [None, "tmp", ("tmp",)])
def test_paths_must_be_a_list(bad):
    with pytest.raises(TypeError):
        cout._check_wipe_paths(paths=bad, root=ROOT, config_path="x.ini")


@pytest.mark.parametrize("bad", [None, "", "  ", 1])
def test_root_must_be_a_non_empty_string(bad):
    with pytest.raises(ValueError):
        cout._check_wipe_paths(paths=[], root=bad, config_path="x.ini")


# ===================
# removal
# ===================


def _tree(tmp_path):
    root = tmp_path / "repo"
    good = root / "tmp" / "archive"
    good.mkdir(parents=True)
    (good / "a.json").write_text("{}")
    keep = root / "tests" / "data"
    keep.mkdir(parents=True)
    (keep / "b.json").write_text("{}")
    return root, good, keep


def test_allowed_paths_are_removed(tmp_path):
    root, good, keep = _tree(tmp_path)
    cout._wipe_paths(paths=[str(good)], root=str(root), config_path="x.ini")
    assert not good.exists()
    assert (keep / "b.json").exists()


@pytest.mark.parametrize("order", ["refused_last", "refused_first"])
def test_one_refused_path_removes_nothing(tmp_path, order):
    root, good, keep = _tree(tmp_path)
    paths = [str(good), str(keep)]
    if order == "refused_first":
        paths.reverse()
    with pytest.raises(ValueError, match="Refusing to wipe"):
        cout._wipe_paths(paths=paths, root=str(root), config_path="x.ini")
    assert (good / "a.json").exists()
    assert (keep / "b.json").exists()


def test_a_missing_allowed_path_is_fine(tmp_path):
    root, good, keep = _tree(tmp_path)
    missing = root / "tmp" / "never_made"
    cout._wipe_paths(paths=[str(missing)], root=str(root), config_path="x.ini")
    assert not missing.exists()
    assert (good / "a.json").exists()
