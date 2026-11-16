"""A reload without append replaces a named-paths group's csvpaths, and
with them the source copies and reports earlier loads left in the group
home (ODCS contracts, Macie wrappers), and the text allow lists earlier
Macie loads wrote to its assets. Otherwise the home, and every Macie
run's _extra_data/macie/ copy of it, describes rules the group no longer
runs (David, 2026-10-31). Appending keeps them; lists stored with
store_list() are kept."""

import os
import shutil

import pytest

from csvpath import CsvPaths

GROUP = "reload_source_copies_test"
NORMATIVE = os.path.join("tests", "macie", "test_resources", "normative")
WITH_LIST = os.path.join(
    NORMATIVE, "09_text_allow_list", "hr-contractor-allow.macie.json"
)
NO_LIST = os.path.join(NORMATIVE, "01_employee_ids", "hr-employee-ids.macie.json")
DATA = os.path.join(NORMATIVE, "09_text_allow_list", "data", "employees.csv")
ODCS = os.path.join("tests", "odcs", "test_resources", "normative")
PLAIN = os.path.join(
    "tests", "csvpaths", "test_resources", "named_paths", "insert.csvpath"
)


@pytest.fixture
def paths():
    p = CsvPaths()
    p.paths_manager.remove_named_paths(GROUP)
    yield p
    p.paths_manager.remove_named_paths(GROUP)
    p.file_manager.remove_named_file(GROUP)


def _home(paths) -> list[str]:
    home = paths.paths_manager.named_paths_home(GROUP)
    return sorted(n for n in os.listdir(home) if os.path.isfile(os.path.join(home, n)))


def _assets(paths) -> list[str]:
    d = paths.paths_manager.asset_manager.assets_dir_path(GROUP)
    return sorted(os.listdir(d)) if os.path.isdir(d) else []


def _list_id(paths) -> str:
    lists = [a for a in _assets(paths) if a.endswith(".txt")]
    assert len(lists) == 1, lists
    return lists[0]


def test_macie_reload_removes_the_old_wrapper_report_and_list(paths) -> None:
    pm = paths.paths_manager
    pm.add_named_paths_from_file(name=GROUP, file_path=WITH_LIST)
    old_list = _list_id(paths)
    assert "hr-contractor-allow.macie.json" in _home(paths)
    pm.add_named_paths_from_file(name=GROUP, file_path=NO_LIST)
    home = _home(paths)
    assert "hr-contractor-allow.macie.json" not in home
    assert "hr-contractor-allow.macie.json.report.json" not in home
    assert "hr-employee-ids.macie.json" in home
    assert "hr-employee-ids.macie.json.report.json" in home
    assert old_list not in _assets(paths)
    assert "macie_catalog.json" in _assets(paths)
    #
    # only source copies and reports go: never the group's own files
    #
    assert "group.csvpaths" in home
    assert "manifest.json" in home


def test_macie_reload_keeps_a_list_stored_otherwise(paths) -> None:
    pm = paths.paths_manager
    pm.add_named_paths_from_file(name=GROUP, file_path=WITH_LIST)
    pm.asset_manager.store_list(name=GROUP, list_name="mine", values=["a", "b"])
    pm.add_named_paths_from_file(name=GROUP, file_path=NO_LIST)
    assert "mine.txt" in _assets(paths)


def test_macie_append_keeps_the_earlier_copies(paths) -> None:
    pm = paths.paths_manager
    pm.add_named_paths_from_file(name=GROUP, file_path=WITH_LIST)
    old_list = _list_id(paths)
    pm.add_named_paths_from_file(name=GROUP, file_path=NO_LIST, append=True)
    home = _home(paths)
    assert "hr-contractor-allow.macie.json" in home
    assert "hr-employee-ids.macie.json" in home
    assert old_list in _assets(paths)


def test_macie_run_after_a_reload_records_only_the_new_rules(paths) -> None:
    pm = paths.paths_manager
    pm.add_named_paths_from_file(name=GROUP, file_path=WITH_LIST)
    old_list = _list_id(paths)
    pm.add_named_paths_from_file(name=GROUP, file_path=NO_LIST)
    paths.file_manager.add_named_file(name=GROUP, path=DATA)
    paths.collect_paths(filename=GROUP, pathsname=GROUP)
    run_dir = paths.results_manager.get_named_results(GROUP)[0].run_dir
    recorded = []
    for root, _, files in os.walk(os.path.join(run_dir, "_extra_data", "macie")):
        recorded.extend(files)
    assert "hr-employee-ids.macie.json" in recorded
    assert "hr-contractor-allow.macie.json" not in recorded
    assert old_list not in recorded


def test_odcs_reload_removes_the_old_contract_and_report(paths, tmp_path) -> None:
    first = tmp_path / "orders-v1.yaml"
    second = tmp_path / "events-v2.yaml"
    shutil.copy(os.path.join(ODCS, "01_orders_simple", "contract.yaml"), first)
    shutil.copy(os.path.join(ODCS, "03_events_dates", "contract.yaml"), second)
    pm = paths.paths_manager
    pm.add_named_paths_from_file(name=GROUP, file_path=str(first))
    assert "orders-v1.yaml" in _home(paths)
    pm.add_named_paths_from_file(name=GROUP, file_path=str(second))
    home = _home(paths)
    assert "orders-v1.yaml" not in home
    assert "orders-v1.yaml.report.json" not in home
    assert "events-v2.yaml" in home
    assert "events-v2.yaml.report.json" in home


def test_plain_reload_over_macie_removes_the_wrapper_copies(paths) -> None:
    pm = paths.paths_manager
    pm.add_named_paths_from_file(name=GROUP, file_path=WITH_LIST)
    pm.add_named_paths_from_file(name=GROUP, file_path=PLAIN)
    home = _home(paths)
    assert not [n for n in home if ".macie.json" in n]
    assert "group.csvpaths" in home
    #
    # documented: the Macie catalog and lists stay in assets, unread, as no
    # Macie run happens without Macie functions
    #
    assert "macie_catalog.json" in _assets(paths)
