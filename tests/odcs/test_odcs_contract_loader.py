import json
import os

import pytest

from csvpath.odcs.odcs_contract_loader import OdcsContractLoader
from csvpath.odcs.odcs_exceptions import OdcsException

PAIR_01 = os.path.join(
    "tests", "odcs", "test_resources", "normative", "01_orders_simple", "contract.yaml"
)


def _minimal(api_version: str = "v3.1.0") -> dict:
    return {
        "apiVersion": api_version,
        "kind": "DataContract",
        "id": "c1",
        "version": "1.0.0",
        "status": "active",
        "schema": [
            {"name": "t", "properties": [{"name": "a", "logicalType": "string"}]}
        ],
    }


def test_odcs_loader_has_a_schema_file_for_every_version() -> None:
    for api_version in OdcsContractLoader.SCHEMAS:
        schema = OdcsContractLoader.schema(api_version=api_version)
        assert api_version in schema["properties"]["apiVersion"]["enum"]


def test_odcs_loader_from_path() -> None:
    contract = OdcsContractLoader.from_path(path=PAIR_01)
    assert contract["id"] == "orders-contract"


def test_odcs_loader_from_path_bad_input() -> None:
    with pytest.raises(ValueError):
        OdcsContractLoader.from_path(path="")
    with pytest.raises(ValueError):
        OdcsContractLoader.from_path(path="no/such/contract.yaml")


def test_odcs_loader_from_string_yaml_and_json() -> None:
    with open(PAIR_01, encoding="utf-8") as f:
        from_yaml = OdcsContractLoader.from_string(text=f.read())
    from_json = OdcsContractLoader.from_string(text=json.dumps(from_yaml))
    assert from_json == from_yaml


def test_odcs_loader_from_string_bad_input() -> None:
    with pytest.raises(ValueError):
        OdcsContractLoader.from_string(text="  ")
    with pytest.raises(TypeError):
        OdcsContractLoader.from_string(text=None)
    with pytest.raises(OdcsException):
        OdcsContractLoader.from_string(text="a: [unclosed")
    with pytest.raises(TypeError):
        OdcsContractLoader.from_string(text="- just\n- a list\n")


@pytest.mark.parametrize(
    "api_version", ["v3.0.0", "v3.0.1", "v3.0.2", "v3.1.0", "v3.2.0"]
)
def test_odcs_loader_validate_supported_versions(api_version: str) -> None:
    contract = _minimal(api_version)
    assert OdcsContractLoader.validate(contract=contract) is contract


@pytest.mark.parametrize("api_version", ["v2.2.2", "v4.0.0", None])
def test_odcs_loader_validate_unsupported_versions(api_version) -> None:
    with pytest.raises(OdcsException):
        OdcsContractLoader.validate(contract=_minimal(api_version))


def test_odcs_loader_validate_schema_invalid() -> None:
    contract = _minimal()
    contract["schema"][0]["properties"][0]["logicalType"] = "text"
    with pytest.raises(OdcsException, match="logicalType"):
        OdcsContractLoader.validate(contract=contract)


def test_odcs_loader_validate_not_a_dict() -> None:
    with pytest.raises(TypeError):
        OdcsContractLoader.validate(contract=[])


def test_odcs_loader_schema_unknown_version() -> None:
    with pytest.raises(ValueError):
        OdcsContractLoader.schema(api_version="v9.9.9")
