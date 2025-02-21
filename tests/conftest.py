import pytest
import os
import shutil
from csvpath import CsvPaths
from csvpath.util.nos import Nos


@pytest.fixture(scope="session", autouse=True)
def clear_files(request):
    paths = CsvPaths()
    config = paths.config
    archive = config.archive_path
    files = config.inputs_files_path
    paths = config.inputs_csvpaths_path
    cache = config.cache_dir_path

    print("cleaning up local ahead of the run")
    for p in [archive, paths, files, cache]:
        if p is None:
            continue
        p = p.strip()
        nos = Nos(p)
        print(f"checking {p} for old test run files")
        if nos.exists():
            print(f"deleting from {p}")
            try:
                nos.remove()
            except Exception as e:
                print(f"Error in cleaning: {type(e)}: {e}")

    print("cleaning complete.")
    print(
        "\nREMEMBER TO CHECK THAT YOUR CONFIG.INI PATHS (IN ./CONFIG/ AND ./TEST/) MATCH SYSTEM SEPARATORS\n\n"
    )
