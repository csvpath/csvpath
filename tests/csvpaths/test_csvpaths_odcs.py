"""ODCS data contracts loaded as named-paths groups.

PathsManager.add_named_paths_from_file() and add_named_paths_from_dir()
accept ODCS contracts (.yml / .yaml). A contract converts to one csvpath
(one table per contract), the contract is copied into the named-paths group
home, and the conversion report is written next to it.

These tests use the normative pairs in tests/odcs/test_resources/normative/,
so the expected csvpaths, reports, and run results are the ones the
converter tests already verify.
"""

import json
import os
import shutil
import subprocess
import sys

import pytest
import yaml

from csvpath import CsvPaths
from csvpath.util.exceptions import FileException, InputException
from csvpath.util.nos import Nos

NORMATIVE = os.path.join("tests", "odcs", "test_resources", "normative")
ORDERS = os.path.join(NORMATIVE, "01_orders_simple")
CRM = os.path.join(NORMATIVE, "02_crm_two_tables")
SHIPMENTS = os.path.join(NORMATIVE, "04_shipments_unsupported")

GROUPS = [
    "odcs_test_orders",
    "odcs_test_shipments",
    "odcs_test_crm",
    "odcs_test_refused",
    "odcs_test_dir",
    "orders_contract",
    "simple_path",
]
NAMED_FILE = "odcs_test_orders_data"


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def _read_yaml(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _group(paths: CsvPaths, name: str) -> list[str]:
    #
    # the group file pads each csvpath with newlines; compare the text
    #
    return [p.strip() for p in paths.paths_manager.get_named_paths(name)]


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


def _add_orders(paths: CsvPaths, *, name: str = "odcs_test_orders") -> str:
    return paths.paths_manager.add_named_paths_from_file(
        name=name, file_path=os.path.join(ORDERS, "contract.yaml")
    )


def _report(paths: CsvPaths, *, name: str, contract: str = "contract.yaml") -> dict:
    home = paths.paths_manager.named_paths_home(name)
    path = Nos(home).join(f"{contract}.report.json")
    assert Nos(path).exists(), f"no report at {path}"
    return json.loads(_read(path))


#
# loading one contract
#


def test_odcs_load_from_file_group_holds_converted_csvpath(paths) -> None:
    ref = _add_orders(paths)
    assert ref is not None
    assert paths.paths_manager.has_named_paths("odcs_test_orders")
    group = _group(paths, "odcs_test_orders")
    expected = _read(os.path.join(ORDERS, "expected", "orders.csvpath")).strip()
    assert group == [expected]


def test_odcs_load_from_file_csvpath_identity_is_table_name(paths) -> None:
    _add_orders(paths)
    ids = [
        t[0] for t in paths.paths_manager.get_identified_paths_in("odcs_test_orders")
    ]
    assert ids == ["orders"]


def test_odcs_load_from_file_copies_contract_byte_for_byte(paths) -> None:
    _add_orders(paths)
    home = paths.paths_manager.named_paths_home("odcs_test_orders")
    copy = Nos(home).join("contract.yaml")
    assert Nos(copy).exists()
    with open(copy, "rb") as f:
        copied = f.read()
    with open(os.path.join(ORDERS, "contract.yaml"), "rb") as f:
        original = f.read()
    assert copied == original


def test_odcs_load_from_file_writes_manifest_entry(paths) -> None:
    _add_orders(paths)
    manifest = paths.paths_manager.get_manifest_for_name("odcs_test_orders")
    assert len(manifest) == 1
    entry = manifest[0]
    assert entry["named_paths_name"] == "odcs_test_orders"
    assert entry["source_path"] == os.path.join(ORDERS, "contract.yaml")
    assert entry["named_paths_count"] == 1
    assert entry["named_paths_identities"] == ["orders"]
    #
    # the group's uuid comes from the manifest. it raised IndexError when
    # the manifest entry was lost.
    #
    assert paths.paths_manager.get_named_paths_uuid("odcs_test_orders") is not None


def test_odcs_load_from_file_writes_report_to_group_home(paths) -> None:
    _add_orders(paths)
    report = _report(paths, name="odcs_test_orders")
    contract = _read_yaml(os.path.join(ORDERS, "contract.yaml"))
    assert report["source_path"] == os.path.join(ORDERS, "contract.yaml")
    assert report["contract_id"] == contract["id"]
    assert report["contract_version"] == contract["version"]
    assert report["api_version"] == contract["apiVersion"]
    assert report["tables"] == ["orders"]
    assert report["skipped"] == []


def test_odcs_load_from_file_report_lists_skipped_items(paths) -> None:
    ref = paths.paths_manager.add_named_paths_from_file(
        name="odcs_test_shipments",
        file_path=os.path.join(SHIPMENTS, "contract.yaml"),
    )
    assert ref is not None
    report = _report(paths, name="odcs_test_shipments")
    expected = _read_yaml(os.path.join(SHIPMENTS, "expected", "report.yaml"))
    keys = ["object", "location", "feature"]
    actual = [{k: s[k] for k in keys} for s in report["skipped"]]
    assert actual == [{k: s[k] for k in keys} for s in expected["skipped"]]
    for s in report["skipped"]:
        assert s["reason"].strip() != ""


def test_odcs_load_from_file_reload_appends_nothing_when_unchanged(paths) -> None:
    _add_orders(paths)
    _add_orders(paths)
    manifest = paths.paths_manager.get_manifest_for_name("odcs_test_orders")
    assert len(manifest) == 1
    assert _group(paths, "odcs_test_orders") == [
        _read(os.path.join(ORDERS, "expected", "orders.csvpath")).strip()
    ]


#
# running a group loaded from a contract
#


def _expected_runs() -> list[dict]:
    return _read_yaml(os.path.join(ORDERS, "expected.yaml"))["runs"]


@pytest.mark.parametrize("run", _expected_runs(), ids=lambda r: r["data"])
def test_odcs_loaded_group_runs_as_expected(paths, run: dict) -> None:
    _add_orders(paths)
    data = os.path.join(ORDERS, "data", run["data"])
    paths.file_manager.add_named_file(name=NAMED_FILE, path=data)
    paths.collect_paths(filename=NAMED_FILE, pathsname="odcs_test_orders")
    results = paths.results_manager.get_named_results("odcs_test_orders")
    assert len(results) == 1
    result = results[0]
    with open(data, encoding="utf-8") as f:
        rows = [line.rstrip("\n").split(",") for line in f]
    expected = [rows[i] for i in run["valid_lines"]]
    assert result.lines.to_list() == expected
    assert result.csvpath.is_valid is run["is_valid"]


#
# one table per contract
#


def test_odcs_load_from_file_rejects_multiple_tables(paths) -> None:
    with pytest.raises(InputException, match="customers, payments"):
        paths.paths_manager.add_named_paths_from_file(
            name="odcs_test_crm", file_path=os.path.join(CRM, "contract.yaml")
        )
    assert not paths.paths_manager.has_named_paths("odcs_test_crm")


#
# local file policy
#


def test_odcs_load_from_file_respects_allow_local_files(paths) -> None:
    paths.config.add_to_config("inputs", "allow_local_files", False)
    try:
        with pytest.raises(FileException):
            paths.paths_manager.add_named_paths_from_file(
                name="odcs_test_refused",
                file_path=os.path.join(ORDERS, "contract.yaml"),
            )
        assert not paths.paths_manager.has_named_paths("odcs_test_refused")
    finally:
        paths.config.add_to_config("inputs", "allow_local_files", True)


#
# loading a directory
#


@pytest.fixture
def contract_dir(tmp_path):
    shutil.copy(
        os.path.join(ORDERS, "contract.yaml"),
        os.path.join(tmp_path, "orders_contract.yaml"),
    )
    with open(os.path.join(tmp_path, "simple_path.csvpath"), "w") as f:
        f.write("$[*][ yes() ]")
    with open(os.path.join(tmp_path, "notes.md"), "w") as f:
        f.write("not a csvpath or a contract")
    return str(tmp_path)


def test_odcs_load_from_dir_one_group_per_file(paths, contract_dir) -> None:
    refs = paths.paths_manager.add_named_paths_from_dir(directory=contract_dir)
    assert len(refs) == 2
    assert None not in refs
    assert _group(paths, "orders_contract") == [
        _read(os.path.join(ORDERS, "expected", "orders.csvpath")).strip()
    ]
    assert _group(paths, "simple_path") == ["$[*][ yes() ]"]
    report = _report(paths, name="orders_contract", contract="orders_contract.yaml")
    assert report["tables"] == ["orders"]


def test_odcs_load_from_dir_rejects_contract_in_named_group(
    paths, contract_dir
) -> None:
    #
    # aggregating contracts would work, but is not supported yet: see #338
    #
    with pytest.raises(
        InputException, match="aggregating ODCS contracts is not yet supported"
    ):
        paths.paths_manager.add_named_paths_from_dir(
            directory=contract_dir, name="odcs_test_dir"
        )
    assert not paths.paths_manager.has_named_paths("odcs_test_dir")


def test_odcs_load_from_dir_named_group_without_contracts_unchanged(
    paths, contract_dir
) -> None:
    os.remove(os.path.join(contract_dir, "orders_contract.yaml"))
    paths.paths_manager.add_named_paths_from_dir(
        directory=contract_dir, name="odcs_test_dir"
    )
    assert _group(paths, "odcs_test_dir") == ["$[*][ yes() ]"]


#
# helpers
#


@pytest.mark.parametrize(
    "path,expected",
    [
        ("a/contract.yaml", True),
        ("contract.yml", True),
        ("a/orders.csvpath", False),
        ("a/orders.csvpaths", False),
        ("yaml", False),
        ("a.yaml.txt", False),
    ],
)
def test_odcs_is_odcs_path(path: str, expected: bool) -> None:
    from csvpath.managers.paths.paths_manager import PathsManager

    assert PathsManager._is_odcs_path(path) is expected


def test_odcs_is_odcs_path_none() -> None:
    from csvpath.managers.paths.paths_manager import PathsManager

    with pytest.raises(ValueError):
        PathsManager._is_odcs_path(None)


@pytest.mark.parametrize("bad", [None, "", "  "])
def test_odcs_get_csvpaths_from_odcs_bad_path(paths, bad) -> None:
    with pytest.raises(ValueError):
        paths.paths_manager._get_csvpaths_from_odcs(bad)


def test_odcs_write_report_bad_args(paths) -> None:
    pm = paths.paths_manager
    with pytest.raises(ValueError):
        pm._write_odcs_report(name=None, file_path="c.yaml", report={})
    with pytest.raises(ValueError):
        pm._write_odcs_report(name="odcs_test_orders", file_path="", report={})
    with pytest.raises(TypeError):
        pm._write_odcs_report(name="odcs_test_orders", file_path="c.yaml", report=[])


def test_odcs_package_is_imported_lazily() -> None:
    code = (
        "import sys\n"
        "from csvpath import CsvPaths\n"
        "CsvPaths().paths_manager\n"
        "print('csvpath.odcs' in sys.modules)\n"
    )
    out = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=True,
        env=os.environ.copy(),
    )
    assert out.stdout.strip().splitlines()[-1] == "False"
