"""MacieGroupLoader: the Macie side of loading a wrapper as a named-paths
group. tests/csvpaths/test_csvpaths_macie.py loads wrappers through
PathsManager."""

import json
import os

import pytest

from csvpath.macie.macie_converter import MacieConverter
from csvpath.macie.macie_exceptions import MacieException
from csvpath.macie.macie_group_loader import MacieGroupLoader
from csvpath.macie.macie_wrapper_loader import MacieWrapperLoader
from csvpath.macie.managed_catalog import ManagedCatalog

PAIR = os.path.join("tests", "macie", "test_resources", "normative", "01_employee_ids")
WRAPPER = os.path.join(PAIR, "hr-employee-ids.macie.json")
WRAPPERS = os.path.join("tests", "macie", "test_resources", "wrappers")


class FakeConfig:
    """just the get() MacieGroupLoader uses"""

    def __init__(self, values: dict) -> None:
        self.values = values

    def get(self, *, section: str, name: str, default=None):
        return self.values.get((section, name), default)


def test_macie_group_loader_convert_file() -> None:
    paths, report, lists, catalog = MacieGroupLoader.convert_file(
        path=WRAPPER, config=None
    )
    wrapper = MacieWrapperLoader.from_path(path=WRAPPER)
    assert paths == [MacieConverter(wrapper=wrapper).convert().csvpath.strip()]
    assert report == {
        "source_path": WRAPPER,
        "name": "hr-employee-ids",
        "origin": "job",
        "job_id": "5d0c4a1e8b7f6e5d4c3b2a1f0e9d8c7b",
        "template_id": None,
        "account_id": "123456789012",
        "region": "us-east-1",
        "downloaded_at": "2026-10-29T17:40:00Z",
        "lists": [],
        "skipped": [],
        "rulesbase": {"overrides_path": None, "applied": []},
    }
    assert lists == {}
    #
    # without a project rulesbase, the packaged catalog
    #
    assert catalog == ManagedCatalog.load().catalog


def test_macie_group_loader_limits_reach_the_csvpath() -> None:
    config = FakeConfig({("macie", "max_findings"): "50", ("macie", "max_detail"): "3"})
    paths, _, _, _ = MacieGroupLoader.convert_file(path=WRAPPER, config=config)
    assert "  macie-max-findings: 50\n" in paths[0]
    assert "  macie-max-detail: 3\n" in paths[0]


def test_macie_group_loader_report_lists_skipped_items() -> None:
    path = os.path.join(WRAPPERS, "job_download.macie.json")
    _, report, lists, _ = MacieGroupLoader.convert_file(path=path, config=None)
    assert report["name"] == "hr-exports-weekly"
    #
    # its text allow list is unreadable: nothing to store
    #
    assert lists == {}
    assert report["lists"] == []
    features = [s["feature"] for s in report["skipped"]]
    assert features[0] == "allowList.s3WordsList.unreadable"
    assert "warning.CDI_DELETED_BUT_SELECTED" in features
    for s in report["skipped"]:
        assert set(s) == {"object", "location", "feature", "reason"}


def test_macie_group_loader_handcrafted_is_named_for_its_file() -> None:
    path = os.path.join(WRAPPERS, "handcrafted_minimal.macie.json")
    paths, report, _, _ = MacieGroupLoader.convert_file(path=path, config=None)
    assert report["name"] == "handcrafted_minimal"
    assert "  id: handcrafted_minimal\n" in paths[0]


TEXT_PAIR = os.path.join(
    "tests", "macie", "test_resources", "normative", "09_text_allow_list"
)
TEXT_WRAPPER = os.path.join(TEXT_PAIR, "hr-contractor-allow.macie.json")
LIST_ID = "c0n7r4a1c7o9r5s3a6l0lw"
ENTRIES = ["emp-234567", "EMP-678901", "EMP-456789"]


def test_macie_group_loader_convert_file_returns_text_lists() -> None:
    paths, report, lists, _ = MacieGroupLoader.convert_file(
        path=TEXT_WRAPPER, config=None
    )
    assert lists == {LIST_ID: ENTRIES}
    assert f'load_list("{LIST_ID}")' in paths[0]
    #
    # names and counts only: the entries stay out of the report
    #
    assert report["lists"] == [{"name": LIST_ID, "entries": 3}]
    assert "EMP-678901" not in json.dumps(report)


def test_macie_group_loader_name_for() -> None:
    wrapper = MacieWrapperLoader.from_path(path=WRAPPER)
    assert MacieGroupLoader.name_for(wrapper=wrapper, path=WRAPPER) is None
    wrapper["aws"]["classificationJob"]["name"] = "HR (weekly)"
    assert MacieGroupLoader.name_for(wrapper=wrapper, path=WRAPPER) == (
        "hr-employee-ids"
    )
    with pytest.raises(MacieException):
        MacieGroupLoader.name_for(wrapper=wrapper, path="x/has space.macie.json")


@pytest.mark.parametrize(
    "values, expected",
    [
        ({}, {"max_findings": 10000, "max_detail": 15}),
        ({("macie", "max_findings"): " 7 "}, {"max_findings": 7, "max_detail": 15}),
        ({("macie", "max_detail"): "0"}, {"max_findings": 10000, "max_detail": 0}),
        ({("macie", "max_detail"): ""}, {"max_findings": 10000, "max_detail": 15}),
    ],
)
def test_macie_group_loader_limits(values: dict, expected: dict) -> None:
    assert MacieGroupLoader.limits(config=FakeConfig(values)) == expected


def test_macie_group_loader_limits_without_config() -> None:
    assert MacieGroupLoader.limits(config=None) == {
        "max_findings": 10000,
        "max_detail": 15,
    }


@pytest.mark.parametrize(
    "values",
    [
        {("macie", "max_findings"): "lots"},
        {("macie", "max_findings"): "0"},
        {("macie", "max_detail"): "-1"},
    ],
)
def test_macie_group_loader_bad_limits(values: dict) -> None:
    with pytest.raises(MacieException):
        MacieGroupLoader.limits(config=FakeConfig(values))


def test_macie_group_loader_convert_file_bad_input() -> None:
    with pytest.raises(ValueError):
        MacieGroupLoader.convert_file(path="", config=None)
    with pytest.raises(ValueError):
        MacieGroupLoader.convert_file(path="rules.json", config=None)


MACIE = {"id": "pii", "macie-origin": "job"}
PLAIN = {"id": "pii"}


@pytest.mark.parametrize(
    "paths",
    [
        [("pii", MACIE)],
        [("pii", MACIE), ("other", PLAIN)],
        #
        # duplicates without a Macie csvpath are housekeeping, not refused
        #
        [("pii", PLAIN), ("pii", PLAIN)],
        [(None, PLAIN), (None, MACIE)],
    ],
)
def test_macie_group_loader_shared_ids_allowed(paths: list) -> None:
    MacieGroupLoader.refuse_shared_ids(group="g", paths=paths)


@pytest.mark.parametrize(
    "paths",
    [
        [("pii", MACIE), ("pii", MACIE)],
        [("pii", MACIE), ("pii", PLAIN)],
        [("pii", PLAIN), ("x", PLAIN), ("pii", MACIE)],
    ],
)
def test_macie_group_loader_shared_ids_refused(paths: list) -> None:
    with pytest.raises(MacieException):
        MacieGroupLoader.refuse_shared_ids(group="g", paths=paths)


def test_macie_group_loader_shared_ids_bad_input() -> None:
    with pytest.raises(TypeError):
        MacieGroupLoader.refuse_shared_ids(group="g", paths=None)


#
# storing text allow lists in a group. PathsManager calls this before it
# loads the csvpath; tests/csvpaths/test_csvpaths_macie.py loads wrappers
#

GROUP = "macie_test_store_lists"


@pytest.fixture
def paths_manager():
    from csvpath import CsvPaths

    pm = CsvPaths().paths_manager
    pm.remove_named_paths(GROUP)
    yield pm
    pm.remove_named_paths(GROUP)


def _stored(pm) -> list[str]:
    text = pm.asset_manager.get_asset_file(GROUP, f"{LIST_ID}.txt")
    return None if text is None else text.splitlines()


def test_macie_group_loader_store_lists_creates_the_group(paths_manager) -> None:
    pm = paths_manager
    assert not pm.has_named_paths(GROUP)
    out = MacieGroupLoader.store_lists(
        paths_manager=pm, name=GROUP, lists={LIST_ID: ENTRIES}, append=False
    )
    assert out == [pm.asset_manager.list_path(name=GROUP, list_name=LIST_ID)]
    assert pm.has_named_paths(GROUP)
    assert _stored(pm) == ENTRIES


@pytest.mark.parametrize("append", [False, True])
def test_macie_group_loader_store_lists_same_entries(paths_manager, append) -> None:
    pm = paths_manager
    for _ in range(2):
        MacieGroupLoader.store_lists(
            paths_manager=pm, name=GROUP, lists={LIST_ID: ENTRIES}, append=append
        )
    assert _stored(pm) == ENTRIES


def test_macie_group_loader_store_lists_append_different_is_refused(
    paths_manager,
) -> None:
    pm = paths_manager
    MacieGroupLoader.store_lists(
        paths_manager=pm, name=GROUP, lists={LIST_ID: ENTRIES}, append=False
    )
    with pytest.raises(MacieException, match=LIST_ID):
        MacieGroupLoader.store_lists(
            paths_manager=pm,
            name=GROUP,
            #
            # the other list is new, and fine, but nothing is written
            #
            lists={"other": ["x"], LIST_ID: ENTRIES[:2]},
            append=True,
        )
    assert _stored(pm) == ENTRIES
    assert pm.asset_manager.get_asset_file(GROUP, "other.txt") is None


def test_macie_group_loader_store_lists_without_append_replaces(
    paths_manager,
) -> None:
    pm = paths_manager
    MacieGroupLoader.store_lists(
        paths_manager=pm, name=GROUP, lists={LIST_ID: ENTRIES}, append=False
    )
    MacieGroupLoader.store_lists(
        paths_manager=pm, name=GROUP, lists={LIST_ID: ["EMP-111111"]}, append=False
    )
    assert _stored(pm) == ["EMP-111111"]


@pytest.mark.parametrize(
    "args, error",
    [
        ({"paths_manager": None}, ValueError),
        ({"name": ""}, ValueError),
        ({"name": None}, ValueError),
        ({"lists": None}, TypeError),
        ({"append": "yes"}, TypeError),
        ({"lists": {"bad name": ["x"]}}, ValueError),
    ],
)
def test_macie_group_loader_store_lists_bad_input(paths_manager, args, error) -> None:
    kwargs = {
        "paths_manager": paths_manager,
        "name": GROUP,
        "lists": {LIST_ID: ENTRIES},
        "append": False,
    }
    kwargs.update(args)
    with pytest.raises(error):
        MacieGroupLoader.store_lists(**kwargs)
    assert not paths_manager.has_named_paths(GROUP)


#
# storing the catalog a group was loaded with (rulesbase-design.md, P2)
#


def _catalog() -> dict:
    return ManagedCatalog.load().catalog


def _snapshot(pm) -> dict | None:
    text = pm.asset_manager.get_asset_file(GROUP, MacieGroupLoader.CATALOG_ASSET)
    return None if text is None else json.loads(text)


def test_macie_group_loader_store_assets_without_lists(paths_manager) -> None:
    #
    # the catalog is stored even when the wrapper has no allow lists
    #
    pm = paths_manager
    MacieGroupLoader.store_assets(
        paths_manager=pm, name=GROUP, lists={}, catalog=_catalog(), append=False
    )
    assert pm.has_named_paths(GROUP)
    assert _snapshot(pm) == _catalog()
    assert _stored(pm) is None


def test_macie_group_loader_store_assets_with_lists(paths_manager) -> None:
    pm = paths_manager
    MacieGroupLoader.store_assets(
        paths_manager=pm,
        name=GROUP,
        lists={LIST_ID: ENTRIES},
        catalog=_catalog(),
        append=False,
    )
    assert _stored(pm) == ENTRIES
    assert _snapshot(pm) == _catalog()


def test_macie_group_loader_store_assets_append_same_catalog(paths_manager) -> None:
    pm = paths_manager
    for _ in range(2):
        MacieGroupLoader.store_assets(
            paths_manager=pm, name=GROUP, lists={}, catalog=_catalog(), append=True
        )
    assert _snapshot(pm) == _catalog()


def test_macie_group_loader_store_assets_append_different_catalog_is_refused(
    paths_manager,
) -> None:
    pm = paths_manager
    MacieGroupLoader.store_assets(
        paths_manager=pm, name=GROUP, lists={}, catalog=_catalog(), append=False
    )
    changed = _catalog()
    changed["keyword_lists"]["br_rg"]["keywords"] = ["registro geral"]
    with pytest.raises(MacieException, match="different managed identifier catalog"):
        MacieGroupLoader.store_assets(
            paths_manager=pm,
            name=GROUP,
            lists={LIST_ID: ENTRIES},
            catalog=changed,
            append=True,
        )
    #
    # nothing written: neither the list nor the catalog
    #
    assert _stored(pm) is None
    assert _snapshot(pm) == _catalog()
    #
    # without append the group's catalog is replaced
    #
    MacieGroupLoader.store_assets(
        paths_manager=pm, name=GROUP, lists={}, catalog=changed, append=False
    )
    assert _snapshot(pm) == changed


@pytest.mark.parametrize(
    "args, error",
    [
        ({"paths_manager": None}, ValueError),
        ({"name": ""}, ValueError),
        ({"catalog": None}, TypeError),
        ({"append": "yes"}, TypeError),
    ],
)
def test_macie_group_loader_store_assets_bad_input(paths_manager, args, error) -> None:
    kwargs = {
        "paths_manager": paths_manager,
        "name": GROUP,
        "lists": {},
        "catalog": _catalog(),
        "append": False,
    }
    kwargs.update(args)
    with pytest.raises(error):
        MacieGroupLoader.store_assets(**kwargs)
    assert not paths_manager.has_named_paths(GROUP)
