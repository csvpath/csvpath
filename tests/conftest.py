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
    local_paths = []
    sftp_paths = []
    s3_paths = []
    for p in [archive, paths, files, cache]:
        if p.startswith("sftp://"):
            sftp_paths.append(p)
        elif p.startswith("s3://"):
            s3_paths.append(p)
        else:
            local_paths.append(p)

    print("cleaning up local ahead of the run")
    for p in local_paths:
        nos = Nos(p)
        print(f"checking {p} for old test run files")
        # if os.path.exists(p):
        if nos.exists():
            print(f"deleting from {p}")
            nos.remove()

        #   print(f"deleting from {p}")
        #   shutil.rmtree(p)

    print("cleaning up local ahead of the run")
    for p in sftp_paths:
        nos = Nos(p)
        print(f"checking {p} for old test run files")
        if nos.exists():
            print(f"deleting from {p}")
            nos.remove()

    print("cleaning up local ahead of the run")
    for p in s3_paths:
        nos = Nos(p)
        print(f"checking {p} for old test run files")
        if nos.exists():
            print(f"deleting from {p}")
            nos.remove()

    print("cleaning complete.")
    print(
        "\nREMEMBER TO CHECK THAT YOUR CONFIG.INI PATHS (IN ./CONFIG/ AND ./TEST/) MATCH SYSTEM SEPARATORS\n\n"
    )
