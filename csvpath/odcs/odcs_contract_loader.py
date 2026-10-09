import json
import logging
import os

import jsonschema
import yaml

from .odcs_exceptions import OdcsException


class OdcsContractLoader:
    """loads an ODCS contract from YAML or JSON text, or a local file, and
    validates it against the official ODCS JSON Schema for its apiVersion.

    Supported apiVersions are v3.0.x, v3.1.0, and v3.2.0. Anything else,
    and any contract that is not schema-valid, raises OdcsException.
    """

    SCHEMA_DIR = os.path.join(os.path.dirname(__file__), "schemas")

    #
    # apiVersion -> schema file. the v3.0.2 schema accepts v3.0.0 and
    # v3.0.1 as apiVersion values too.
    #
    SCHEMAS = {
        "v3.0.0": "odcs-json-schema-v3.0.2.json",
        "v3.0.1": "odcs-json-schema-v3.0.2.json",
        "v3.0.2": "odcs-json-schema-v3.0.2.json",
        "v3.1.0": "odcs-json-schema-v3.1.0.json",
        "v3.2.0": "odcs-json-schema-v3.2.0.json",
    }

    @classmethod
    def logger(cls) -> logging.Logger:
        return logging.getLogger(cls.__name__)

    @classmethod
    def from_path(cls, *, path: str) -> dict:
        if not isinstance(path, str) or path.strip() == "":
            raise ValueError("path must be a non-empty str")
        if not os.path.isfile(path):
            raise ValueError(f"No ODCS contract file at {path}")
        with open(path, encoding="utf-8") as f:
            return cls.from_string(text=f.read())

    @classmethod
    def from_string(cls, *, text: str) -> dict:
        if not isinstance(text, str):
            raise TypeError(f"text must be a str, not {type(text)}")
        if text.strip() == "":
            raise ValueError("text cannot be empty")
        try:
            #
            # JSON is a subset of YAML, so one parser handles both
            #
            contract = yaml.safe_load(text)
        except yaml.YAMLError as e:
            cls.logger().error("Cannot parse ODCS contract: %s", e)
            raise OdcsException(f"Cannot parse ODCS contract: {e}") from e
        return cls.validate(contract=contract)

    @classmethod
    def validate(cls, *, contract: dict) -> dict:
        if not isinstance(contract, dict):
            raise TypeError(f"An ODCS contract must be a dict, not {type(contract)}")
        api_version = contract.get("apiVersion")
        if api_version not in cls.SCHEMAS:
            msg = (
                f"Unsupported ODCS apiVersion {api_version}. "
                f"Supported: {', '.join(cls.SCHEMAS)}"
            )
            cls.logger().error(msg)
            raise OdcsException(msg)
        schema = cls.schema(api_version=api_version)
        validator = jsonschema.validators.validator_for(schema)(schema)
        errors = sorted(validator.iter_errors(contract), key=lambda e: list(e.path))
        if errors:
            details = "; ".join(
                f"{'/'.join(str(p) for p in e.path) or '<root>'}: {e.message}"
                for e in errors[:5]
            )
            msg = f"ODCS contract is not valid {api_version}: {details}"
            cls.logger().error(msg)
            raise OdcsException(msg)
        return contract

    @classmethod
    def schema(cls, *, api_version: str) -> dict:
        if api_version not in cls.SCHEMAS:
            raise ValueError(f"No ODCS schema for apiVersion {api_version}")
        path = os.path.join(cls.SCHEMA_DIR, cls.SCHEMAS[api_version])
        with open(path, encoding="utf-8") as f:
            return json.load(f)
