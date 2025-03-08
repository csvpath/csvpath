import pytest
import os
import shutil
from csvpath import CsvPaths
from csvpath.util.nos import Nos


@pytest.fixture(scope="session", autouse=True)
def clear_files(request):
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

    paths = CsvPaths()
    config = paths.config
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
        print(f"Checking {p} ")
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
