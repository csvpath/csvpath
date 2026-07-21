import pytest
import os
import traceback
from csvpath import CsvPaths
from csvpath.util.box import Box
from csvpath.util.config import Config
from csvpath.util.nos import Nos


# conftest.py
import gc
import sqlite3


def _live_connections():
    return {id(o): o for o in gc.get_objects() if isinstance(o, sqlite3.Connection)}


@pytest.fixture(autouse=True)
def _sqlite_leak_probe(request):
    before = set(_live_connections())
    yield
    after = _live_connections()
    for i in set(after) - before:
        conn = after[i]
        try:
            rows = conn.execute("PRAGMA database_list").fetchall()
        except sqlite3.ProgrammingError:
            continue  # already closed cleanly, not a leak
        raise Exception(
            f"\n### sqlite3.Connection still open after {request.node.nodeid}"
        )
        print("    database_list:", rows)


def pytest_sessionfinish(session, exitstatus):
    if Box.SQL_ENGINE in Box.STUFF:
        try:
            box = Box()
            engine = box.get(key=Box.SQL_ENGINE)
            engine.dispose()
            box.remove(Box.SQL_ENGINE)
        except Exception as e:
            print(f"Error in test cleanup: {type(e)}: {e}")


@pytest.fixture(scope="function", autouse=True)
def has_ini(request):
    OINI = os.getenv(Config.CSVPATH_CONFIG_FILE_ENV)
    if OINI is None:
        raise ValueError("OINI cannot be None")


@pytest.fixture(scope="session", autouse=True)
def wipe_local_test_artifacts(request):
    _wipe_local_test_artifacts()


def _wipe_local_test_artifacts():
    #
    # a hard, filesystem-level reset of everything a local-backend test run
    # can leave behind. this runs once, before the session's tests start --
    # not after -- so that a run's own artifacts (logs, archived results,
    # cache) stay on disk for postmortem inspection right up until the next
    # run begins, but every run still starts from a genuinely empty state.
    #
    # this is deliberately blunter than _clear_files()'s manager-level
    # deregistration below. the managers intentionally leave top-level
    # directories, manifest.json files, and other record-of-the-past
    # artifacts behind when a named thing is removed -- that is correct
    # production behavior (e.g. removing the last named file should not
    # destroy the registration history), but it is not what a clean test
    # slate wants.
    #
    csvpaths = CsvPaths()
    config = csvpaths.config
    sqlite_db = config.get(
        section="sqlite", name="db", default=f"archive{os.sep}csvpath.db"
    )
    paths = [
        config.cache_dir_path,
        config.archive_path,
        config.transfer_root,
        config.inputs_files_path,
        config.inputs_csvpaths_path,
        os.path.dirname(sqlite_db),
        os.path.dirname(config.log_file),
        #
        # not config-driven: parquet() falls back to a hardcoded relative
        # "parquet" dir for standalone (non-CsvPaths) runs -- see
        # csvpath/csvpath issue #184, tracked separately as its own gap.
        #
        "parquet",
    ]
    for p in paths:
        if not p:
            continue
        nos = Nos(p)
        if not nos.is_local:
            # never touch a remote (s3/azure/gcs/sftp) path from here
            continue
        if nos.dir_exists():
            nos.remove()


@pytest.fixture(scope="session", autouse=True)
def clear_files(request, wipe_local_test_artifacts):
    _clear_files()


def _clear_files():
    try:
        e = os.environ["CSVPATH_CONFIG_PATH"]
        print(f"\nEnvironment-set config path: {e}")
    except Exception:
        print(traceback.format_exc())

    csvpaths = CsvPaths()

    config = csvpaths.config
    print(f"LOADED CONFIG PATH IS: {config.config_path}")
    print("Cleaning up ahead of the run")

    names = csvpaths.paths_manager.named_paths_names
    for name in names:
        csvpaths.paths_manager.remove_named_paths(name)

    names = csvpaths.file_manager.named_file_names
    for name in names:
        csvpaths.file_manager.remove_named_file(name)

    names = csvpaths.results_manager.list_named_results()
    for name in names:
        csvpaths.results_manager.remove_named_results(name)
