import pytest

from csvpath import CsvPaths
from csvpath.managers.files.file_manager import FileManager
from csvpath.managers.paths.paths_manager import PathsManager
from csvpath.managers.results.results_manager import ResultsManager
from csvpath.managers.run.run_registrar import RunRegistrar

#
# RC triage A19 part 3 (David, 2026-11-16): the four root-ledger readers
# raise a ValueError naming the ledger and the likely cause when it does
# not parse. They raised a bare json.JSONDecodeError.
#


@pytest.fixture
def corrupt(tmp_path):
    path = tmp_path / "manifest.json"
    path.write_text('{}  [{"uuid": "u1"}]')
    return str(path)


@pytest.mark.parametrize(
    "cls, path_property, reader",
    [
        (FileManager, "files_root_manifest_path", "files_root_manifest"),
        (PathsManager, "paths_root_manifest_path", "paths_root_manifest"),
        (ResultsManager, "results_root_manifest_path", "results_root_manifest"),
    ],
)
def test_a_corrupt_root_ledger_names_itself(monkeypatch, corrupt, cls, path_property, reader):
    monkeypatch.setattr(cls, path_property, property(lambda self: corrupt))
    paths = CsvPaths()
    manager = {
        FileManager: paths.file_manager,
        PathsManager: paths.paths_manager,
        ResultsManager: paths.results_manager,
    }[cls]
    with pytest.raises(ValueError, match="holds more than one JSON value") as e:
        getattr(manager, reader)
    assert corrupt in str(e.value)


def test_a_corrupt_archive_run_manifest_names_itself(monkeypatch, corrupt, tmp_path):
    # built without __init__: only the archive dir and the ledger path matter
    registrar = RunRegistrar.__new__(RunRegistrar)
    registrar.archive = str(tmp_path)
    monkeypatch.setattr(RunRegistrar, "manifest_path", property(lambda self: corrupt))
    with pytest.raises(ValueError, match="holds more than one JSON value"):
        registrar.manifest
