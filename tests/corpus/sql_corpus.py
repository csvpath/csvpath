"""Builds (or rebuilds) a private copy of the reference-v3 test corpus with SQL
capture on, OUTSIDE the repo, for exploring references in the CLI.

Usage:
    ~/dev/csvpath/.venv/bin/python ~/dev/csvpath/tests/corpus/sql_corpus.py <target dir> [--sql on|shadow]

The target gets:
    config/config.ini   the corpus config, every path pointed into the target,
                        the sql listener group on, SQLite, [references] sql
    data/               the corpus, generated from assets.yaml, and the SQLite
                        database (data/csvpath-sqlite.db)
    .csvpath_sql_corpus a marker: this script only reuses a folder it made

Re-running wipes and rebuilds data/ and rewrites config/config.ini. Every
path in the config is absolute, so a moved or copied folder still points at
the original: build a new one instead. Nothing else in the target is touched, and nothing in the repo is written:
assets.yaml and the source files are only read. It uses generate.py's own
build_events() and run_events() (as test_corpus_under_shadow.py does), not
generate.main(), which writes the committed tests/corpus/data/.

Deletes are guarded (see check_target() and _wipe()): the target must be
outside the repo, not an ancestor of it, not / or the home folder, not a
symlink, and either new, empty, or marked by this script. The repo and the
home folder are compared by identity, not spelling. data/ and .scratch/ must
be real folders and config/ a real folder in the target; every path is
checked before any is removed.

At the end it checks the SQL tables have rows and that a few references
resolve the same with [references] sql off and on, and prints the CLI command.
"""

import argparse
import os
import shlex
import shutil
import sqlite3
import sys
from configparser import RawConfigParser
from pathlib import Path

CORPUS_DIR = Path(__file__).resolve().parent
REPO_ROOT = CORPUS_DIR.parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(CORPUS_DIR))

import yaml  # noqa: E402

import generate  # noqa: E402
from csvpath import CsvPaths  # noqa: E402
from csvpath.references.reference_finder_factory_3 import (  # noqa: E402
    ReferenceFinderFactory3,
)
from csvpath.util.box import Box  # noqa: E402

MARKER = ".csvpath_sql_corpus"
MARKER_TEXT = "made by tests/corpus/sql_corpus.py; safe for it to rebuild\n"
CORPUS_CONFIG = CORPUS_DIR / "config" / "config.ini"
CORPUS_DATA_PREFIX = "tests/corpus/data"
CORPUS_CONFIG_PREFIX = "tests/corpus/config/config.ini"
MAIN_CONFIG = REPO_ROOT / "config" / "config.ini"
SQL_MODES = ("on", "shadow")
#
# the folders a rebuild removes, inside the target
#
WIPED = ("data", ".scratch")
#
# made again under data/ after a wipe, as generate.reset_data_dir() does
#
DATA_FOLDERS = (
    "inputs/named_files",
    "inputs/named_paths",
    "archive",
    "logs",
    "cache",
    "transfers",
)
#
# references checked with sql off and on after a build
#
CHECKS = [
    "$*.files.:manifest():last()",
    "$*.csvpaths.:manifest():last()",
    "$*.results.:manifest():last()",
    "$*.files.:flatten().:last()",
    "$*.results.:last()",
]


def _same(a: Path, b: Path) -> bool:
    """whether two paths are the same folder on disk. By identity, not by
    spelling: on a case-insensitive file system '~/DEV/CSVPATH' is the repo
    though realpath() keeps the case it is given (reviewer on #811)."""
    try:
        return os.path.samefile(a, b)
    except OSError:
        return False


def _first_existing(path: Path) -> Path:
    """path, or its nearest ancestor that exists"""
    while not path.exists() and path != path.parent:
        path = path.parent
    return path


def check_target(target: "str | Path") -> Path:
    """the resolved target folder, or ValueError if it is not safe to build
    in. Safe: outside the repo and not an ancestor of it, not / or the home
    folder or a folder directly under /, not a symlink, and either missing,
    empty, or marked by this script. The repo and home are compared by
    identity (_same()), so letter case or another spelling cannot get past."""
    if target is None or str(target).strip() == "":
        raise ValueError("A target folder is required")
    raw = Path(str(target)).expanduser()
    if raw.is_symlink():
        raise ValueError(f"Refusing {raw}: it is a symlink")
    resolved = Path(os.path.realpath(raw))
    home = Path(os.path.realpath(Path.home()))
    repo = Path(os.path.realpath(REPO_ROOT))
    if len(resolved.parts) < 3 or resolved == home or _same(resolved, home):
        raise ValueError(f"Refusing {resolved}: too high up the file system")
    existing = _first_existing(resolved)
    if any(_same(folder, repo) for folder in (existing, *existing.parents)):
        raise ValueError(f"Refusing {resolved}: it is inside the repo {repo}")
    if resolved.exists() and any(_same(resolved, folder) for folder in repo.parents):
        raise ValueError(f"Refusing {resolved}: the repo {repo} is inside it")
    if resolved.exists():
        if not resolved.is_dir():
            raise ValueError(f"Refusing {resolved}: it is not a folder")
        if any(resolved.iterdir()) and not _is_marked(resolved):
            raise ValueError(
                f"Refusing {resolved}: it is not empty and this script did not "
                f"make it (no {MARKER}). Use a new or empty folder."
            )
    return resolved


def _is_marked(folder: Path) -> bool:
    marker = folder / MARKER
    return (
        marker.is_file()
        and not marker.is_symlink()
        and marker.read_text(encoding="utf-8") == MARKER_TEXT
    )


def _wipe(*, target: Path) -> None:
    """removes the WIPED folders inside a checked target. Each is checked
    before any is removed: a direct child of the target, not a symlink, a
    folder. A file there raised NotADirectoryError after data/ was gone
    (reviewer on #811)."""
    if target is None:
        raise ValueError("target cannot be None")
    if not _is_marked(target):
        raise ValueError(f"Refusing to wipe in {target}: no {MARKER}")
    doomed = []
    for name in WIPED:
        path = target / name
        if path.is_symlink():
            raise ValueError(f"Refusing to wipe {path}: it is a symlink")
        if Path(os.path.realpath(path)).parent != target:
            raise ValueError(f"Refusing to wipe {path}: it leads out of {target}")
        if path.exists() and not path.is_dir():
            raise ValueError(f"Refusing to wipe {path}: it is not a folder")
        if path.exists():
            doomed.append(path)
    for path in doomed:
        shutil.rmtree(path)


def write_config(*, target: Path, sql: str) -> Path:
    """config/config.ini in the target: the corpus config with its paths
    pointed into the target, the sql listener group on (its listeners as in
    config/config.ini), SQLite in data/, and [references] sql. Returns its
    path."""
    if target is None:
        raise ValueError("target cannot be None")
    if sql not in SQL_MODES:
        raise ValueError(f"sql must be one of {SQL_MODES}, not {sql!r}")
    config = RawConfigParser()
    config.optionxform = str
    config.read(CORPUS_CONFIG, encoding="utf-8")
    path = target / "config" / "config.ini"
    data = target / "data"
    for section in config.sections():
        for key, value in config.items(section):
            value = value.replace(CORPUS_CONFIG_PREFIX, str(path))
            value = value.replace(CORPUS_DATA_PREFIX, str(data))
            config.set(section, key, value)
    left = [
        f"[{s}] {k}"
        for s in config.sections()
        for k, v in config.items(s)
        if "tests/corpus" in v
    ]
    if left:
        raise ValueError(
            f"The corpus config has paths this script does not move: {left}"
        )
    main = RawConfigParser()
    main.optionxform = str
    main.read(MAIN_CONFIG, encoding="utf-8")
    listeners = {k: v for k, v in main.items("listeners") if k.startswith("sql.")}
    if not listeners:
        raise ValueError(f"No sql.* listeners in {MAIN_CONFIG}")
    groups = [
        g.strip() for g in config.get("listeners", "groups").split(",") if g.strip()
    ]
    if "sql" not in groups:
        groups.append("sql")
    config.set("listeners", "groups", ", ".join(groups))
    for key, value in listeners.items():
        config.set("listeners", key, value)
    for section in ("sql", "references"):
        if not config.has_section(section):
            config.add_section(section)
    config.set("sql", "dialect", "sqlite")
    config.set("sql", "connection_string", f"sqlite:///{data / 'csvpath-sqlite.db'}")
    config.set("references", "sql", sql)
    _check_config_path(target=target, path=path)
    path.parent.mkdir(exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        config.write(f)
    return path


def _check_config_path(*, target: Path, path: Path) -> None:
    """raises unless config/ and config/config.ini, if they exist, are a real
    folder and file in the target: a symlink there would have the config
    written over a file elsewhere (reviewer on #811)"""
    if target is None or path is None:
        raise ValueError("target and path are required")
    folder = path.parent
    for p in (folder, path):
        if p.is_symlink():
            raise ValueError(f"Refusing to write {p}: it is a symlink")
    if folder.exists() and (
        not folder.is_dir() or Path(os.path.realpath(folder)).parent != target
    ):
        raise ValueError(f"Refusing to write in {folder}: not a folder in {target}")
    if path.exists() and not path.is_file():
        raise ValueError(f"Refusing to write {path}: it is not a file")


def _events() -> list:
    """the corpus events, with each named-paths source made absolute: they
    are written relative to the repo root, and the build runs in the target"""
    events = generate.build_events(yaml.safe_load(generate.ASSETS_PATH.read_text()))
    fixed = []
    for offset_days, kind, payload in events:
        if kind == "paths" and not Path(payload["source"]).is_absolute():
            payload = dict(payload, source=str(REPO_ROOT / payload["source"]))
        fixed.append((offset_days, kind, payload))
    return fixed


def _clear_engine() -> None:
    # a cached engine would keep another config's database
    box = Box()
    engine = box.get(key=Box.SQL_ENGINE)
    if engine is not None:
        engine.dispose()
        box.remove(Box.SQL_ENGINE)


def build(*, target, sql: str = "on") -> dict:
    """(re)builds the corpus in `target` and returns a summary: the target,
    the config path, the row count of each SQL table, and the references
    that resolved differently with sql off and on (empty when they agree).
    Restores the working directory and CSVPATH_CONFIG_PATH."""
    if sql not in SQL_MODES:
        raise ValueError(f"sql must be one of {SQL_MODES}, not {sql!r}")
    target = check_target(target)
    target.mkdir(parents=True, exist_ok=True)
    (target / MARKER).write_text(MARKER_TEXT, encoding="utf-8")
    _wipe(target=target)
    config_path = write_config(target=target, sql=sql)
    for folder in DATA_FOLDERS:
        (target / "data" / folder).mkdir(parents=True)
    scratch = target / ".scratch"
    scratch.mkdir()
    cwd = os.getcwd()
    previous = os.environ.get("CSVPATH_CONFIG_PATH")
    os.environ["CSVPATH_CONFIG_PATH"] = str(config_path)
    _clear_engine()
    try:
        os.chdir(target)
        p = CsvPaths()
        try:
            generate.run_events(p, _events(), scratch_dir=scratch)
        finally:
            generate.reset_now()
        shutil.rmtree(scratch)
        differ = _compare(p)
    finally:
        _clear_engine()
        os.chdir(cwd)
        if previous is None:
            os.environ.pop("CSVPATH_CONFIG_PATH", None)
        else:
            os.environ["CSVPATH_CONFIG_PATH"] = previous
    return {
        "target": target,
        "config": config_path,
        "tables": _table_counts(target / "data" / "csvpath-sqlite.db"),
        "differ": differ,
    }


def _compare(p: CsvPaths) -> list:
    """the CHECKS that query differently with sql off and on, or that find
    nothing, since empty agreeing with empty would show nothing"""
    if p is None:
        raise ValueError("p cannot be None")
    mode = p.config.references_sql
    differ = []
    try:
        for reference in CHECKS:
            seen = []
            for value in ("off", "on"):
                p.config.add_to_config(section="references", key="sql", value=value)
                finder = ReferenceFinderFactory3.for_reference(
                    reference=reference, csvpaths=p
                )
                seen.append([(str(r.path), r.uuid) for r in finder.query().results])
            if seen[0] != seen[1] or not seen[0]:
                differ.append(reference)
    finally:
        p.config.add_to_config(section="references", key="sql", value=mode)
    return differ


def _table_counts(db: Path) -> dict:
    if db is None:
        raise ValueError("db cannot be None")
    if not db.is_file():
        raise ValueError(f"No SQLite database at {db}: the sql listeners wrote nothing")
    connection = sqlite3.connect(db)
    try:
        names = [
            n
            for (n,) in connection.execute(
                "select name from sqlite_master where type='table' order by name"
            )
        ]
        return {
            n: connection.execute(f'select count(*) from "{n}"').fetchone()[0]
            for n in names
        }
    finally:
        connection.close()


def _cli_command() -> str:
    """the CLI of the Python running this script: its venv is the one with
    csvpath installed"""
    cli = Path(sys.executable).parent / "cli"
    if cli.is_file():
        return shlex.quote(str(cli))
    python = shlex.quote(sys.executable)
    return f'{python} -c "from csvpath.cli.cli import run; run()"'


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("target", help="the folder to build in, outside the repo")
    parser.add_argument(
        "--sql", choices=SQL_MODES, default="on", help="[references] sql"
    )
    args = parser.parse_args()
    try:
        summary = build(target=args.target, sql=args.sql)
    except ValueError as e:
        print(f"Nothing was built: {e}", file=sys.stderr)
        return 2
    print(f"Corpus built in {summary['target']}")
    for table, count in summary["tables"].items():
        print(f"  {table}: {count} rows")
    if summary["differ"]:
        print(
            f"SQL off and on DIFFER, or found nothing, for: {summary['differ']}",
            file=sys.stderr,
        )
        return 1
    print(f"SQL off and on agree on {len(CHECKS)} references.")
    print("\nRun the CLI from there:")
    print(f"  cd {shlex.quote(str(summary['target']))}")
    print(
        f"  CSVPATH_CONFIG_PATH={shlex.quote(str(summary['config']))} {_cli_command()}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
