"""MacieGroupLoader: the Macie side of loading a wrapper as a named-paths
group. tests/csvpaths/test_csvpaths_macie.py loads wrappers through
PathsManager."""

import os

import pytest

from csvpath.macie.macie_converter import MacieConverter
from csvpath.macie.macie_exceptions import MacieException
from csvpath.macie.macie_group_loader import MacieGroupLoader
from csvpath.macie.macie_wrapper_loader import MacieWrapperLoader

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
    paths, report = MacieGroupLoader.convert_file(path=WRAPPER, config=None)
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
        "skipped": [],
    }


def test_macie_group_loader_limits_reach_the_csvpath() -> None:
    config = FakeConfig({("macie", "max_findings"): "50", ("macie", "max_detail"): "3"})
    paths, _ = MacieGroupLoader.convert_file(path=WRAPPER, config=config)
    assert "  macie-max-findings: 50\n" in paths[0]
    assert "  macie-max-detail: 3\n" in paths[0]


def test_macie_group_loader_report_lists_skipped_items() -> None:
    path = os.path.join(WRAPPERS, "job_download.macie.json")
    _, report = MacieGroupLoader.convert_file(path=path, config=None)
    assert report["name"] == "hr-exports-weekly"
    features = [s["feature"] for s in report["skipped"]]
    assert features[0] == "allowList.s3WordsList"
    assert "warning.CDI_DELETED_BUT_SELECTED" in features
    for s in report["skipped"]:
        assert set(s) == {"object", "location", "feature", "reason"}


def test_macie_group_loader_handcrafted_is_named_for_its_file() -> None:
    path = os.path.join(WRAPPERS, "handcrafted_minimal.macie.json")
    paths, report = MacieGroupLoader.convert_file(path=path, config=None)
    assert report["name"] == "handcrafted_minimal"
    assert "  id: handcrafted_minimal\n" in paths[0]


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
