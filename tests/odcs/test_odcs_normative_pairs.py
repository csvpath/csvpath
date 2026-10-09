"""Normative ODCS -> CsvPath pairs.

Each directory under tests/odcs/test_resources/normative/ is one pair:

    contract.yaml     an ODCS data contract (input to the converter)
    expected/*.csvpath  the csvpath(s) the converter must produce, one per
                      schema object
    data/*.csv        sample data with known conforming and non-conforming lines
    expected.yaml     which lines of which data file each expected csvpath
                      must match, and the expected is_valid

These tests do not exercise the converter. They pin down the pairs
themselves, so we develop the converter against verified targets:

    - every contract is valid against the official ODCS JSON Schema for its
      apiVersion
    - every expected csvpath, run against its data, matches exactly the
      conforming lines and ends with the expected is_valid

Converter tests compare their output to these same pairs.
"""

import csv
import json
import os
import re

import jsonschema
import pytest
import yaml

from csvpath import CsvPath

RESOURCES = os.path.join("tests", "odcs", "test_resources")
NORMATIVE = os.path.join(RESOURCES, "normative")
SCHEMAS = os.path.join(RESOURCES, "schema")


def _pair_dirs() -> list[str]:
    return sorted(
        os.path.join(NORMATIVE, d)
        for d in os.listdir(NORMATIVE)
        if os.path.isdir(os.path.join(NORMATIVE, d))
    )


def _runs() -> list[tuple[str, dict]]:
    runs = []
    for pair in _pair_dirs():
        with open(os.path.join(pair, "expected.yaml"), encoding="utf-8") as f:
            expected = yaml.safe_load(f)
        for run in expected["runs"]:
            runs.append((pair, run))
    return runs


def _run_id(param) -> str:
    if isinstance(param, dict):
        return f"{param['csvpath']}-{param['data']}"
    return os.path.basename(param)


def _with_data_path(*, csvpath: str, data_path: str) -> str:
    #
    # expected csvpaths have no filename in their root, as the converter's
    # output will not. add one so the csvpath can run stand-alone.
    #
    with_path, n = re.subn(r"\$\[", f"${data_path}[", csvpath, count=1)
    if n != 1:
        raise ValueError(f"No root found in csvpath: {csvpath}")
    return with_path


def _data_lines(data_path: str) -> list[list[str]]:
    with open(data_path, encoding="utf-8", newline="") as f:
        return list(csv.reader(f))


@pytest.mark.parametrize("pair", _pair_dirs(), ids=_run_id)
def test_odcs_normative_contract_is_schema_valid(pair: str) -> None:
    with open(os.path.join(pair, "contract.yaml"), encoding="utf-8") as f:
        contract = yaml.safe_load(f)
    api_version = contract["apiVersion"]
    schema_path = os.path.join(SCHEMAS, f"odcs-json-schema-{api_version}.json")
    assert os.path.exists(schema_path), f"No ODCS schema fixture for {api_version}"
    with open(schema_path, encoding="utf-8") as f:
        schema = json.load(f)
    validator = jsonschema.validators.validator_for(schema)(schema)
    errors = [e.message for e in validator.iter_errors(contract)]
    assert errors == []


@pytest.mark.parametrize("pair,run", _runs(), ids=_run_id)
def test_odcs_normative_expected_csvpath_behavior(pair: str, run: dict) -> None:
    with open(
        os.path.join(pair, "expected", run["csvpath"]), encoding="utf-8"
    ) as f:
        csvpath = f.read()
    data_path = os.path.join(pair, "data", run["data"])
    path = CsvPath()
    matched = path.collect(_with_data_path(csvpath=csvpath, data_path=data_path))
    lines = _data_lines(data_path)
    expected = [lines[i] for i in run["valid_lines"]]
    assert matched == expected
    assert path.is_valid is run["is_valid"]
