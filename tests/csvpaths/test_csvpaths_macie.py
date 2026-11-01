"""Macie wrappers loaded as named-paths groups.

PathsManager.add_named_paths_from_file() and add_named_paths_from_dir()
accept Macie wrappers (.macie.json). A wrapper converts to one csvpath, the
wrapper is copied into the named-paths group home, and the conversion
report is written next to it, as for ODCS contracts.

A Macie csvpath's id must be unique in its group, so an append that would
share one is refused. Other duplicate ids are still allowed.

These tests use the normative pair in tests/macie/test_resources/normative/,
so the expected run results are the ones the converter tests already verify.
"""

import csv
import json
import os
import shutil
import subprocess
import sys

import pytest
import yaml

from csvpath import CsvPaths
from csvpath.macie.macie_converter import MacieConverter
from csvpath.macie.macie_exceptions import MacieException
from csvpath.macie.macie_wrapper_loader import MacieWrapperLoader
from csvpath.util.exceptions import InputException
from csvpath.util.nos import Nos

PAIR = os.path.join("tests", "macie", "test_resources", "normative", "01_employee_ids")
WRAPPER_FILE = "hr-employee-ids.macie.json"
WRAPPER = os.path.join(PAIR, WRAPPER_FILE)
ORDERS_CONTRACT = os.path.join(
    "tests", "odcs", "test_resources", "normative", "01_orders_simple", "contract.yaml"
)

GROUPS = ["macie_test_hr", "macie_test_mixed", "macie_test_dir", "hr-employee-ids"]
NAMED_FILE = "macie_test_employees"


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def _group(paths: CsvPaths, name: str) -> list[str]:
    return [p.strip() for p in paths.paths_manager.get_named_paths(name)]


def _ids(paths: CsvPaths, name: str) -> list[str]:
    return [t[0] for t in paths.paths_manager.get_identified_paths_in(name)]


def _remove_groups(paths: CsvPaths) -> None:
    for name in GROUPS:
        paths.paths_manager.remove_named_paths(name)
    paths.file_manager.remove_named_file(NAMED_FILE)


@pytest.fixture
def paths():
    p = CsvPaths()
    _remove_groups(p)
    yield p
    _remove_groups(p)


def _add_hr(paths: CsvPaths, *, name: str = "macie_test_hr", append=False) -> str:
    return paths.paths_manager.add_named_paths_from_file(
        name=name, file_path=WRAPPER, append=append
    )


def _converted() -> str:
    wrapper = MacieWrapperLoader.from_path(path=WRAPPER)
    return MacieConverter(wrapper=wrapper).convert().csvpath.strip()


def _plain(tmp_path, *, identity: str = "simple") -> str:
    p = tmp_path / f"{identity}.csvpath"
    p.write_text(f"~ id: {identity} ~\n$[*][ yes() ]\n", encoding="utf-8")
    return str(p)


#
# loading one wrapper
#


def test_macie_load_from_file_group_holds_converted_csvpath(paths) -> None:
    assert _add_hr(paths) is not None
    assert _group(paths, "macie_test_hr") == [_converted()]
    assert _ids(paths, "macie_test_hr") == ["hr-employee-ids"]


def test_macie_load_from_file_copies_wrapper_byte_for_byte(paths) -> None:
    _add_hr(paths)
    home = paths.paths_manager.named_paths_home("macie_test_hr")
    copy = Nos(home).join(WRAPPER_FILE)
    assert Nos(copy).exists()
    with open(copy, "rb") as f, open(WRAPPER, "rb") as g:
        assert f.read() == g.read()


def test_macie_load_from_file_writes_report_to_group_home(paths) -> None:
    _add_hr(paths)
    home = paths.paths_manager.named_paths_home("macie_test_hr")
    report = json.loads(_read(Nos(home).join(f"{WRAPPER_FILE}.report.json")))
    assert report["source_path"] == WRAPPER
    assert report["name"] == "hr-employee-ids"
    assert report["origin"] == "job"
    assert report["job_id"] == "5d0c4a1e8b7f6e5d4c3b2a1f0e9d8c7b"
    assert report["skipped"] == []


def test_macie_load_from_file_writes_manifest_entry(paths) -> None:
    _add_hr(paths)
    manifest = paths.paths_manager.get_manifest_for_name("macie_test_hr")
    assert len(manifest) == 1
    entry = manifest[0]
    assert entry["source_path"] == WRAPPER
    assert entry["named_paths_identities"] == ["hr-employee-ids"]
    assert entry["named_paths_count"] == 1


def test_macie_load_from_file_reload_appends_nothing_when_unchanged(paths) -> None:
    _add_hr(paths)
    _add_hr(paths)
    assert len(paths.paths_manager.get_manifest_for_name("macie_test_hr")) == 1
    assert _group(paths, "macie_test_hr") == [_converted()]


def test_macie_load_uses_config_limits(paths) -> None:
    paths.config.set(section="macie", name="max_detail", value="3")
    _add_hr(paths)
    assert "  macie-max-detail: 3\n" in _group(paths, "macie_test_hr")[0]


def test_macie_load_plain_json_is_not_a_wrapper() -> None:
    assert CsvPaths().paths_manager._is_macie_path("x/hr.macie.json") is True
    assert CsvPaths().paths_manager._is_macie_path("x/definition.json") is False
    assert CsvPaths().paths_manager._is_macie_path("x/macie.json") is False
    with pytest.raises(ValueError):
        CsvPaths().paths_manager._is_macie_path(None)


#
# running a group loaded from a wrapper
#


def test_macie_loaded_group_runs_as_expected(paths) -> None:
    #
    # the pair's expected results use a detail cap of 3
    #
    paths.config.set(section="macie", name="max_detail", value="3")
    _add_hr(paths)
    data = os.path.join(PAIR, "data", "employees.csv")
    paths.file_manager.add_named_file(name=NAMED_FILE, path=data)
    paths.collect_paths(filename=NAMED_FILE, pathsname="macie_test_hr")
    results = paths.results_manager.get_named_results("macie_test_hr")
    assert len(results) == 1
    result = results[0]
    with open(os.path.join(PAIR, "expected.yaml"), encoding="utf-8") as f:
        run = yaml.safe_load(f)["runs"][0]
    with open(data, encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))
    assert result.lines.to_list() == [rows[i] for i in run["finding_lines"]]
    with open(os.path.join(PAIR, "expected", "printouts.macie.txt")) as f:
        assert result.get_printouts("macie") == f.read().splitlines()
    errors = [{"line": e.line_count, "message": e.message} for e in result.errors]
    assert errors == run["errors"]
    with open(os.path.join(PAIR, "expected", "findings.json")) as f:
        assert result.csvpath.variables["macie_findings"] == json.load(f)


#
# appending
#


def test_macie_append_to_a_group_with_other_csvpaths(paths, tmp_path) -> None:
    #
    # a plain csvpath, then an ODCS contract, then a Macie wrapper
    #
    pm = paths.paths_manager
    pm.add_named_paths_from_file(name="macie_test_mixed", file_path=_plain(tmp_path))
    pm.add_named_paths_from_file(
        name="macie_test_mixed", file_path=ORDERS_CONTRACT, append=True
    )
    _add_hr(paths, name="macie_test_mixed", append=True)
    assert _ids(paths, "macie_test_mixed") == ["simple", "orders", "hr-employee-ids"]
    home = pm.named_paths_home("macie_test_mixed")
    for f in ["contract.yaml", WRAPPER_FILE]:
        assert Nos(Nos(home).join(f)).exists()
        assert Nos(Nos(home).join(f"{f}.report.json")).exists()


def test_macie_append_same_wrapper_twice_is_refused(paths) -> None:
    _add_hr(paths)
    with pytest.raises(MacieException):
        _add_hr(paths, append=True)
    #
    # refused before anything was written
    #
    assert _group(paths, "macie_test_hr") == [_converted()]
    assert len(paths.paths_manager.get_manifest_for_name("macie_test_hr")) == 1


def test_macie_append_plain_csvpath_with_a_macie_id_is_refused(paths, tmp_path) -> None:
    _add_hr(paths)
    with pytest.raises(MacieException):
        paths.paths_manager.add_named_paths_from_file(
            name="macie_test_hr",
            file_path=_plain(tmp_path, identity="hr-employee-ids"),
            append=True,
        )
    assert _ids(paths, "macie_test_hr") == ["hr-employee-ids"]


def test_macie_append_wrapper_onto_a_plain_csvpath_with_its_id_is_refused(
    paths, tmp_path
) -> None:
    paths.paths_manager.add_named_paths_from_file(
        name="macie_test_mixed", file_path=_plain(tmp_path, identity="hr-employee-ids")
    )
    with pytest.raises(MacieException):
        _add_hr(paths, name="macie_test_mixed", append=True)


def test_macie_reload_without_append_replaces_the_group(paths) -> None:
    #
    # without append the group is rewritten, so the same wrapper is fine
    #
    _add_hr(paths)
    paths.config.set(section="macie", name="max_detail", value="4")
    _add_hr(paths)
    assert _ids(paths, "macie_test_hr") == ["hr-employee-ids"]


def test_macie_duplicate_plain_ids_are_still_allowed(paths, tmp_path) -> None:
    pm = paths.paths_manager
    p = _plain(tmp_path)
    pm.add_named_paths_from_file(name="macie_test_mixed", file_path=p)
    pm.add_named_paths_from_file(name="macie_test_mixed", file_path=p, append=True)
    assert _ids(paths, "macie_test_mixed") == ["simple", "simple"]


#
# loading a directory
#


@pytest.fixture
def wrapper_dir(tmp_path):
    d = tmp_path / "rules"
    d.mkdir()
    shutil.copy(WRAPPER, d / WRAPPER_FILE)
    return str(d)


def test_macie_load_from_dir_names_the_group_without_the_suffix(
    paths, wrapper_dir
) -> None:
    refs = paths.paths_manager.add_named_paths_from_dir(directory=wrapper_dir)
    assert len(refs) == 1
    #
    # not hr-employee-ids.macie: a dot in a group name breaks references
    #
    assert paths.paths_manager.has_named_paths("hr-employee-ids")
    assert _ids(paths, "hr-employee-ids") == ["hr-employee-ids"]


def test_macie_load_from_dir_refuses_aggregating_a_wrapper(paths, wrapper_dir) -> None:
    with pytest.raises(InputException):
        paths.paths_manager.add_named_paths_from_dir(
            directory=wrapper_dir, name="macie_test_dir"
        )


#
# the Macie package is only imported when needed
#


def test_macie_package_is_imported_lazily(tmp_path) -> None:
    code = (
        "import sys\n"
        "from csvpath import CsvPaths\n"
        "CsvPaths().paths_manager\n"
        "print('csvpath.macie' in sys.modules)\n"
    )
    out = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=True,
        env=os.environ.copy(),
    )
    assert out.stdout.strip().splitlines()[-1] == "False"
