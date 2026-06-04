import pytest
import os
import traceback
from csvpath import CsvPaths
from csvpath.util.box import Box
from csvpath.util.config import Config


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
