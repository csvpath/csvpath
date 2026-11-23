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
        if p.is_file() and "__pycache__" not in p.parts
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


@pytest.mark.parametrize("target", ["/", "/Users", "~"])
def test_the_top_of_the_file_system_and_home_are_refused(target):
    with pytest.raises(ValueError, match="too high up|the repo"):
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
    cwd = os.getcwd()
    previous = os.environ.get("CSVPATH_CONFIG_PATH")
    target = tmp_path_factory.mktemp("sql_corpus") / "corpus"
    summary = sql_corpus.build(target=target)
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
        return {
            m.parent.name: len(json.loads(m.read_text()))
            for m in sorted((root / "inputs" / "named_files").glob("*/manifest.json"))
        }

    assert counts(target / "data") == counts(CORPUS_DIR / "data")
    assert counts(target / "data")


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
