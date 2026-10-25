"""FilesListener must use the config it is given, i.e. the CsvPaths
instance's runtime config, not a fresh Config() from the default config
file.

The registrar loads additional listeners with config= only and sets
csvpaths afterwards. FilesListener used to discard that config, so the
root named-files ledger (inputs/named_files/manifest.json) went to the
default config's [inputs] files path, ignoring add_to_config changes.

Everything is written under pytest's tmp_path.
"""

import json

import pytest

from csvpath import CsvPaths
from csvpath.managers.files.files_listener import FilesListener


@pytest.fixture
def paths(tmp_path):
    p = CsvPaths()
    p.config.add_to_config(
        section="inputs", key="files", value=str(tmp_path / "named_files")
    )
    p.config.add_to_config(
        section="inputs", key="csvpaths", value=str(tmp_path / "named_paths")
    )
    p.config.add_to_config(
        section="results", key="archive", value=str(tmp_path / "archive")
    )
    p.config.add_to_config(section="listeners", key="groups", value="default")
    return p


def test_config_only_is_kept(paths):
    lst = FilesListener(config=paths.config)
    assert lst.config is paths.config


def test_csvpaths_only_uses_its_config(paths):
    lst = FilesListener(csvpaths=paths)
    assert lst.config is paths.config


def test_both_uses_the_csvpaths_config(paths):
    lst = FilesListener(csvpaths=paths, config=paths.config)
    assert lst.config is paths.config


def test_csvpaths_set_after_init_keeps_config(paths):
    #
    # how Registrar.load_additional_listener builds it
    #
    lst = FilesListener(config=paths.config)
    lst.csvpaths = paths
    assert lst.config is paths.config


def test_manifest_path_uses_the_given_config(paths, tmp_path):
    lst = FilesListener(config=paths.config)
    mf = lst.manifest_path()
    assert mf == str(tmp_path / "named_files" / "manifest.json")


def test_registration_writes_the_root_ledger_under_the_runtime_config(
    paths, tmp_path
):
    csv = tmp_path / "people.csv"
    csv.write_text("firstname,lastname\nfred,flintstone\n", encoding="utf-8")
    ref = paths.file_manager.add_named_file(name="people", path=str(csv))
    assert ref is not None
    mf = tmp_path / "named_files" / "manifest.json"
    assert mf.exists()
    with open(mf, "r", encoding="utf-8") as f:
        entries = json.load(f)
    assert len(entries) == 1
    assert entries[0]["named_file_name"] == "people"
