import pytest
import os
import shutil
from csvpath import CsvPaths


@pytest.fixture(scope="session", autouse=True)
def clear_files(request):
    paths = CsvPaths()
    config = paths.config
    archive = config.archive_path
    files = config.inputs_files_path
    paths = config.inputs_csvpaths_path
    cache = config.cache_dir_path
    paths = [archive, paths, files, cache]

    print("cleaning up ahead of the run")
    for p in paths:
        if os.path.exists(p):
            print(f"deleting from {p}")
            shutil.rmtree(p)

    print("cleaning complete.")
    print("\nREMEMBER TO CHECK THAT YOUR CONFIG.INI PATHS MATCH SYSTEM SEPARATORS\n\n")
