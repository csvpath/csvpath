import pytest
import os
import shutil
import traceback
from csvpath import CsvPaths
from csvpath.util.nos import Nos
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
    print("checking OINI")
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
    """
    if os.sep == "\\":

        e = ""
        if os.path.exists("conf.env"):
            with open("conf.env", "r", encoding="utf-8") as file:
                e = file.read()
                e = e.strip()
        else:
            e = f"assets{os.sep}config{os.sep}jenkins-local-windows.ini"
        print(f"\nConftest: clear_files: env setup: e: {e}")
        os.environ["CSVPATH_CONFIG_PATH"] = e
    """
    paths = CsvPaths()
    config = paths.config
    print(f"LOADED CONFIG PATH IS: {config.config_path}")
    archive = config.archive_path
    files = config.inputs_files_path
    paths = config.inputs_csvpaths_path
    cache = config.cache_dir_path

    print("Cleaning up ahead of the run")
    nos = Nos(None)
    for p in [archive, paths, files, cache]:
        if p is None:
            continue
        p = p.strip()
        nos.path = p
        print(f"Checking {p}")

        if nos.dir_exists():
            print(f"Deleting from {p}")
            try:
                nos.remove()
            except Exception as e:
                print(f"Error in cleaning {p}: {type(e)}: {e}")

    config._assure_archive_path()
    print("Clean-up complete.")
    print(
        "\nREMEMBER TO CHECK THAT CONFIG.INI PATHS (IN ./CONFIG/ AND ./TEST/) MATCH SYSTEM SEPARATORS\n\n"
    )
