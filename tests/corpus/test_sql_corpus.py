"""tests/corpus/sql_corpus.py: the guards on where it builds and what it
deletes, the config it writes, and one real build into a temp folder that
leaves the committed corpus untouched."""

import json
import os
import sys
from configparser import RawConfigParser
from pathlib import Path

import pytest

CORPUS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CORPUS_DIR))

import sql_corpus  # noqa: E402

REPO_ROOT = sql_corpus.REPO_ROOT
#
# making a symlink needs privileges on Windows
#
needs_symlinks = pytest.mark.skipif(
    sys.platform == "win32", reason="symlinks need privileges on Windows"
)


def _marked(folder: Path) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / sql_corpus.MARKER).write_text(sql_corpus.MARKER_TEXT, encoding="utf-8")
    return folder


def _snapshot(root: Path) -> dict:
    """every file under root: size and modification time"""
    return {
        str(p.relative_to(root)): (p.stat().st_size, p.stat().st_mtime_ns)
        for p in sorted(root.rglob("*"))
        if p.is_file() and "__pycache__" not in p.parts and p.name != ".DS_Store"
    }


# ===================
# where it may build
# ===================


@pytest.mark.parametrize("target", [None, "", "  "])
def test_a_target_is_required(target):
    with pytest.raises(ValueError, match="required"):
        sql_corpus.check_target(target)


@pytest.mark.parametrize(
    "target",
    [
        REPO_ROOT,
        REPO_ROOT / "tests" / "corpus" / "data",
        REPO_ROOT / "not_made_yet",
    ],
)
def test_the_repo_and_anything_in_it_are_refused(target):
    with pytest.raises(ValueError, match="inside the repo"):
        sql_corpus.check_target(target)


def test_a_folder_holding_the_repo_is_refused():
    with pytest.raises(ValueError, match="the repo .* is inside it"):
        sql_corpus.check_target(REPO_ROOT.parent)


@pytest.mark.parametrize("target", ["/", "/Users"])
def test_the_top_of_the_file_system_is_refused(target):
    with pytest.raises(ValueError, match="too high up"):
        sql_corpus.check_target(target)


def test_the_home_folder_is_refused(tmp_path, monkeypatch):
    # a home that does not hold the repo, so only the home check can refuse
    home = tmp_path / "home"
    home.mkdir()
    # '~' is expanded from HOME, and the check reads Path.home()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(Path, "home", lambda: home)
    with pytest.raises(ValueError, match="too high up"):
        sql_corpus.check_target("~")
    with pytest.raises(ValueError, match="too high up"):
        sql_corpus.check_target(home)


def test_a_dot_dot_into_the_repo_is_refused():
    with pytest.raises(ValueError, match="inside the repo"):
        sql_corpus.check_target(REPO_ROOT / "tests" / ".." / "not_made_yet")


@pytest.fixture
def fake_repo(tmp_path, monkeypatch):
    repo = tmp_path / "FakeRepo"
    (repo / "tests").mkdir(parents=True)
    monkeypatch.setattr(sql_corpus, "REPO_ROOT", repo)
    return repo


def test_another_spelling_of_the_repo_is_refused(fake_repo):
    # macOS file systems ignore case, and realpath() keeps the case it is
    # given, so the repo is compared by identity (reviewer on #811)
    upper = fake_repo.parent / "FAKEREPO"
    if not upper.exists():
        pytest.skip("this file system is case-sensitive")
    with pytest.raises(ValueError, match="inside the repo"):
        sql_corpus.check_target(upper / "new")
    with pytest.raises(ValueError, match="inside the repo"):
        sql_corpus.check_target(upper)


@needs_symlinks
def test_a_symlinked_parent_into_the_repo_is_refused(fake_repo, tmp_path):
    link = tmp_path / "link"
    link.symlink_to(fake_repo)
    with pytest.raises(ValueError, match="inside the repo"):
        sql_corpus.check_target(link / "new")


def test_a_relative_target_is_from_the_working_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert sql_corpus.check_target("rel") == Path(os.path.realpath(tmp_path / "rel"))


@needs_symlinks
def test_a_symlinked_marker_does_not_count(tmp_path):
    real = tmp_path / "real_marker"
    real.write_text(sql_corpus.MARKER_TEXT, encoding="utf-8")
    target = tmp_path / "t"
    target.mkdir()
    (target / sql_corpus.MARKER).symlink_to(real)
    with pytest.raises(ValueError, match="not empty"):
        sql_corpus.check_target(target)


@needs_symlinks
def test_a_symlink_is_refused(tmp_path):
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real)
    with pytest.raises(ValueError, match="symlink"):
        sql_corpus.check_target(link)


def test_a_file_is_refused(tmp_path):
    f = tmp_path / "a_file"
    f.write_text("x")
    with pytest.raises(ValueError, match="not a folder"):
        sql_corpus.check_target(f)


def test_a_target_under_a_file_is_refused(tmp_path):
    (tmp_path / "afile").write_text("x")
    with pytest.raises(ValueError, match="is not a folder"):
        sql_corpus.check_target(tmp_path / "afile" / "sub")


def test_a_hard_linked_config_is_refused_and_not_written_through(tmp_path):
    outside = tmp_path / "outside.ini"
    outside.write_text("PRECIOUS")
    target = _marked(tmp_path / "t")
    (target / "config").mkdir()
    os.link(outside, target / "config" / "config.ini")
    with pytest.raises(ValueError, match="hard-linked"):
        sql_corpus.write_config(target=target, sql="on")
    assert outside.read_text() == "PRECIOUS"


def test_a_folder_with_something_in_it_is_refused(tmp_path):
    (tmp_path / "keep.txt").write_text("mine")
    with pytest.raises(ValueError, match="not empty"):
        sql_corpus.check_target(tmp_path)


def test_a_marker_with_other_text_does_not_count(tmp_path):
    (tmp_path / sql_corpus.MARKER).write_text("something else")
    with pytest.raises(ValueError, match="not empty"):
        sql_corpus.check_target(tmp_path)


def test_a_new_an_empty_and_a_marked_folder_are_accepted(tmp_path):
    new = tmp_path / "new"
    assert sql_corpus.check_target(new) == Path(os.path.realpath(new))
    empty = tmp_path / "empty"
    empty.mkdir()
    assert sql_corpus.check_target(empty) == Path(os.path.realpath(empty))
    marked = _marked(tmp_path / "marked")
    (marked / "data").mkdir()
    assert sql_corpus.check_target(marked) == Path(os.path.realpath(marked))


# ===================
# what it deletes
# ===================


def test_the_wipe_needs_the_marker(tmp_path):
    (tmp_path / "data").mkdir()
    with pytest.raises(ValueError, match="no .csvpath_sql_corpus"):
        sql_corpus._wipe(target=tmp_path)
    assert (tmp_path / "data").is_dir()


def test_the_wipe_removes_data_and_scratch_only(tmp_path):
    target = _marked(tmp_path / "t")
    (target / "data" / "archive").mkdir(parents=True)
    (target / ".scratch").mkdir()
    (target / "notes.txt").write_text("mine")
    (target / "config").mkdir()
    sql_corpus._wipe(target=target)
    assert not (target / "data").exists()
    assert not (target / ".scratch").exists()
    assert (target / "notes.txt").read_text() == "mine"
    assert (target / "config").is_dir()
    assert (target / sql_corpus.MARKER).is_file()


@needs_symlinks
def test_a_symlinked_data_folder_is_refused_and_nothing_is_removed(tmp_path):
    # every path is checked before any is removed: .scratch survives too
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    (elsewhere / "precious.txt").write_text("keep")
    target = _marked(tmp_path / "t")
    (target / "data").symlink_to(elsewhere)
    (target / ".scratch").mkdir()
    with pytest.raises(ValueError, match="symlink"):
        sql_corpus._wipe(target=target)
    assert (elsewhere / "precious.txt").read_text() == "keep"
    assert (target / ".scratch").is_dir()


@pytest.mark.parametrize("name", ["data", ".scratch"])
def test_a_file_where_a_wiped_folder_goes_is_refused_and_nothing_is_removed(
    tmp_path, name
):
    # every path is checked first: data/ survived a .scratch file only
    # because of this (reviewer on #811)
    target = _marked(tmp_path / "t")
    other = ".scratch" if name == "data" else "data"
    (target / other).mkdir()
    (target / other / "keep.txt").write_text("keep")
    (target / name).write_text("a file")
    with pytest.raises(ValueError, match="not a folder"):
        sql_corpus._wipe(target=target)
    assert (target / other / "keep.txt").read_text() == "keep"
    assert (target / name).read_text() == "a file"


# ===================
# the config it writes
# ===================


@pytest.fixture
def written(tmp_path):
    target = _marked(tmp_path / "t")
    path = sql_corpus.write_config(target=target, sql="on")
    config = RawConfigParser()
    config.optionxform = str
    config.read(path, encoding="utf-8")
    return target, path, config


def test_every_path_is_in_the_target(written):
    target, path, config = written
    values = [v for s in config.sections() for _, v in config.items(s)]
    assert not [v for v in values if "tests/corpus" in v]
    assert config.get("config", "path") == str(path)
    for section, key in [
        ("inputs", "files"),
        ("inputs", "csvpaths"),
        ("results", "archive"),
        ("cache", "path"),
        ("logging", "log_file"),
    ]:
        assert config.get(section, key).startswith(str(target / "data")), key


def test_the_sql_listeners_and_references_are_on(written):
    target, _, config = written
    groups = [g.strip() for g in config.get("listeners", "groups").split(",")]
    assert "default" in groups and "sql" in groups
    sql_keys = [k for k, _ in config.items("listeners") if k.startswith("sql.")]
    assert sql_keys
    assert config.get("sql", "dialect") == "sqlite"
    assert config.get("sql", "connection_string") == (
        f"sqlite:///{target / 'data' / 'csvpath-sqlite.db'}"
    )
    assert config.get("references", "sql") == "on"


@needs_symlinks
@pytest.mark.parametrize("which", ["folder", "file"])
def test_a_symlinked_config_is_refused_and_not_written_through(tmp_path, which):
    victim = tmp_path / "victim"
    victim.mkdir()
    (victim / "config.ini").write_text("PRECIOUS")
    target = _marked(tmp_path / "t")
    if which == "folder":
        (target / "config").symlink_to(victim)
    else:
        (target / "config").mkdir()
        (target / "config" / "config.ini").symlink_to(victim / "config.ini")
    with pytest.raises(ValueError, match="symlink"):
        sql_corpus.write_config(target=target, sql="on")
    assert (victim / "config.ini").read_text() == "PRECIOUS"


def test_shadow_can_be_chosen_and_nothing_else(tmp_path):
    target = _marked(tmp_path / "t")
    path = sql_corpus.write_config(target=target, sql="shadow")
    assert "sql = shadow" in path.read_text()
    with pytest.raises(ValueError, match="sql must be one of"):
        sql_corpus.write_config(target=target, sql="off")


# ===================
# a real build
# ===================


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    committed = _snapshot(CORPUS_DIR)
    top = sorted(p.name for p in REPO_ROOT.iterdir())
    cwd = os.getcwd()
    previous = os.environ.get("CSVPATH_CONFIG_PATH")
    target = tmp_path_factory.mktemp("sql_corpus") / "corpus"
    summary = sql_corpus.build(target=target)
    assert sorted(p.name for p in REPO_ROOT.iterdir()) == top
    return target, summary, committed, cwd, previous


def test_the_build_leaves_the_repo_and_the_process_as_they_were(built):
    _, _, committed, cwd, previous = built
    assert _snapshot(CORPUS_DIR) == committed
    assert os.getcwd() == cwd
    assert os.environ.get("CSVPATH_CONFIG_PATH") == previous


def test_the_sql_tables_have_rows_and_off_and_on_agree(built):
    _, summary, _, _, _ = built
    tables = summary["tables"]
    for table in ("named_file_ledger", "named_paths_ledger", "instance_run"):
        assert tables.get(table, 0) > 0, table
    assert summary["differ"] == []


def test_the_corpus_matches_the_committed_one(built):
    # the same registrations per named-file as tests/corpus/data
    target, _, _, _, _ = built

    def counts(root: Path) -> dict:
        manifests = {
            kind: {
                m.parent.name: len(json.loads(m.read_text()))
                for m in sorted((root / "inputs" / kind).glob("*/manifest.json"))
            }
            for kind in ("named_files", "named_paths")
        }
        runs = {
            group.name: len([d for d in group.iterdir() if d.is_dir()])
            for group in sorted((root / "archive").iterdir())
            if group.is_dir()
        }
        return {**manifests, "runs": runs}

    mine = counts(target / "data")
    assert mine == counts(CORPUS_DIR / "data")
    assert mine["named_files"] and mine["named_paths"] and mine["runs"]


def test_a_rebuild_is_the_same_and_keeps_other_files(built):
    target, summary, _, _, _ = built
    (target / "notes.txt").write_text("mine")
    again = sql_corpus.build(target=target)
    assert again["tables"] == summary["tables"]
    assert (target / "notes.txt").read_text() == "mine"


def test_a_build_into_a_foreign_folder_changes_nothing(tmp_path):
    (tmp_path / "keep.txt").write_text("mine")
    before = _snapshot(tmp_path)
    with pytest.raises(ValueError, match="not empty"):
        sql_corpus.build(target=tmp_path)
    assert _snapshot(tmp_path) == before
