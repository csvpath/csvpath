import pytest
import os
import traceback
from csvpath import CsvPaths
from csvpath.util.box import Box
from csvpath.util.config import Config


import sqlite3

_tracked = []
_orig_connect = sqlite3.connect


def _tracking_connect(*args, **kwargs):
    conn = _orig_connect(*args, **kwargs)
    _tracked.append({"conn": conn, "stack": "".join(traceback.format_stack()[:-1])})
    return conn


sqlite3.connect = _tracking_connect


def pytest_sessionfinish(session, exitstatus):
    ###
    for entry in _tracked:
        try:
            entry["conn"].execute("SELECT 1")
        except sqlite3.ProgrammingError:
            continue  # already closed properly
        print("\n### sqlite3 connection never closed, opened at:\n", entry["stack"])

    ###
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
def clear_files(request):
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
