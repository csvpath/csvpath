"""RunInputs: a group run's Macie inputs copied into the run's
_extra_data/macie (specs/macie/rulesbase-design.md, P2b). Real runs are in
tests/csvpaths/test_csvpaths_macie.py; here, the copy rules on their own,
with a stand-in csvpath."""

import json
import os
from types import SimpleNamespace

import pytest

from csvpath import CsvPaths
from csvpath.macie.macie_exceptions import MacieException
from csvpath.macie.run_inputs import RunInputs

PAIR = os.path.join(
    "tests", "macie", "test_resources", "normative", "09_text_allow_list"
)
WRAPPER = os.path.join(PAIR, "hr-contractor-allow.macie.json")
GROUP = "macie_test_run_inputs"


@pytest.fixture
def paths():
    p = CsvPaths()
    p.paths_manager.remove_named_paths(GROUP)
    p.paths_manager.add_named_paths_from_file(name=GROUP, file_path=WRAPPER)
    yield p
    p.paths_manager.remove_named_paths(GROUP)


def _csvpath(paths, run_dir) -> SimpleNamespace:
    return SimpleNamespace(csvpaths=paths, named_paths_name=GROUP, run_dir=str(run_dir))


def test_macie_run_inputs_copied(paths, tmp_path) -> None:
    d = RunInputs.record(csvpath=_csvpath(paths, tmp_path))
    assert d == os.path.join(str(tmp_path), "_extra_data", "macie")
    index = json.loads((tmp_path / "_extra_data" / "macie" / "inputs.json").read_text())
    assert index["group"] == GROUP
    assert set(index["files"]) == {
        "hr-contractor-allow.macie.json",
        "hr-contractor-allow.macie.json.report.json",
        "macie_catalog.json",
        "lists/c0n7r4a1c7o9r5s3a6l0lw.txt",
    }
    copied = RunInputs.inputs(paths_manager=paths.paths_manager, group=GROUP)
    assert {k: RunInputs.sha256(text=v) for k, v in copied.items()} == index["files"]


def test_macie_run_inputs_second_record_checks(paths, tmp_path) -> None:
    csvpath = _csvpath(paths, tmp_path)
    RunInputs.record(csvpath=csvpath)
    index = tmp_path / "_extra_data" / "macie" / "inputs.json"
    before = index.read_text()
    #
    # unchanged: nothing rewritten
    #
    RunInputs.record(csvpath=csvpath)
    assert index.read_text() == before
    #
    # a list changed mid-run: refused
    #
    paths.paths_manager.asset_manager.store_list(
        name=GROUP, list_name="c0n7r4a1c7o9r5s3a6l0lw", values=["EMP-000000"]
    )
    with pytest.raises(MacieException, match="changed during the run"):
        RunInputs.record(csvpath=csvpath)


def test_macie_run_inputs_standalone_writes_nothing(tmp_path) -> None:
    for c in [
        SimpleNamespace(csvpaths=None, named_paths_name=None, run_dir=str(tmp_path)),
        SimpleNamespace(
            csvpaths=object(), named_paths_name=None, run_dir=str(tmp_path)
        ),
        SimpleNamespace(csvpaths=object(), named_paths_name="g", run_dir=None),
    ]:
        assert RunInputs.record(csvpath=c) is None
    assert list(tmp_path.iterdir()) == []


def test_macie_run_inputs_bad_input() -> None:
    with pytest.raises(ValueError):
        RunInputs.record(csvpath=None)
    with pytest.raises(TypeError):
        RunInputs.sha256(text=None)
