import json
import logging
import os
from collections import Counter

import jsonschema

from .macie_exceptions import MacieException
from csvpath.util.nos import Nos
from csvpath.util.file_readers import DataFileReader


class MacieWrapperLoader:
    """loads a CsvPath Macie wrapper (a `*.macie.json` file) and checks it.

    The JSON Schema in schemas/ checks structure. This class then checks
    what a schema cannot: that the selection, the resolved managed data
    identifiers, and the custom identifier and allow list entries all line
    up. Anything wrong raises MacieException. See
    specs/macie/wrapper-format.md for the format.
    """

    SUFFIX = ".macie.json"
    MARKER = "csvpath_macie"
    SCHEMA_DIR = os.path.join(os.path.dirname(__file__), "schemas")

    #
    # format version -> schema file
    #
    SCHEMAS = {1: "csvpath-macie-wrapper-v1.json"}

    @classmethod
    def logger(cls) -> logging.Logger:
        return logging.getLogger(cls.__name__)

    @classmethod
    def is_wrapper_path(cls, *, path: str) -> bool:
        if not isinstance(path, str):
            raise TypeError(f"path must be a str, not {type(path)}")
        return path.endswith(cls.SUFFIX)

    @classmethod
    def from_path(cls, *, path: str) -> dict:
        if not isinstance(path, str) or path.strip() == "":
            raise ValueError("path must be a non-empty str")
        if not cls.is_wrapper_path(path=path):
            raise ValueError(
                f"A Macie wrapper file name must end in {cls.SUFFIX}: {path}"
            )
        if not Nos(path).exists():
            raise ValueError(f"No Macie wrapper file at {path}")
        with DataFileReader(path) as f:
            return cls.from_string(text=f.source.read())

    @classmethod
    def from_string(cls, *, text: str) -> dict:
        if not isinstance(text, str):
            raise TypeError(f"text must be a str, not {type(text)}")
        if text.strip() == "":
            raise ValueError("text cannot be empty")
        try:
            wrapper = json.loads(text)
        except json.JSONDecodeError as e:
            cls.logger().error("Cannot parse Macie wrapper: %s", e)
            raise MacieException(f"Cannot parse Macie wrapper: {e}") from e
        return cls.validate(wrapper=wrapper)

    @classmethod
    def validate(cls, *, wrapper: dict) -> dict:
        if not isinstance(wrapper, dict):
            raise TypeError(f"A Macie wrapper must be a dict, not {type(wrapper)}")
        version = wrapper.get(cls.MARKER)
        if version is None:
            cls._fail(f"Not a Macie wrapper: no {cls.MARKER} key")
        #
        # bool is an int in Python; true must not pass as version 1
        #
        if isinstance(version, bool) or version not in cls.SCHEMAS:
            cls._fail(
                f"Unsupported Macie wrapper version {version!r}. "
                f"Supported: {', '.join(str(v) for v in cls.SCHEMAS)}"
            )
        cls._validate_schema(wrapper=wrapper, version=version)
        cls._validate_source_and_selection(wrapper=wrapper)
        cls._validate_managed(wrapper=wrapper)
        cls._validate_entries(
            wrapper=wrapper,
            entries_key="customDataIdentifiers",
            selected_key="customDataIdentifierIds",
            id_of=lambda e: e["id"],
        )
        cls._validate_entries(
            wrapper=wrapper,
            entries_key="allowLists",
            selected_key="allowListIds",
            id_of=lambda e: e["settings"]["id"],
        )
        cls._validate_allow_list_contents(wrapper=wrapper)
        return wrapper

    @classmethod
    def schema(cls, *, version: int) -> dict:
        if version not in cls.SCHEMAS:
            raise ValueError(f"No Macie wrapper schema for version {version}")
        path = os.path.join(cls.SCHEMA_DIR, cls.SCHEMAS[version])
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def _fail(cls, msg: str) -> None:
        cls.logger().error(msg)
        raise MacieException(msg)

    @classmethod
    def _validate_schema(cls, *, wrapper: dict, version: int) -> None:
        schema = cls.schema(version=version)
        validator = jsonschema.validators.validator_for(schema)(schema)
        errors = sorted(validator.iter_errors(wrapper), key=lambda e: list(e.path))
        if errors:
            details = "; ".join(
                f"{'/'.join(str(p) for p in e.path) or '<root>'}: {e.message}"
                for e in errors[:5]
            )
            cls._fail(f"Macie wrapper is not valid version {version}: {details}")

    @classmethod
    def _validate_source_and_selection(cls, *, wrapper: dict) -> None:
        #
        # a template always means "the recommended set, plus includes,
        # minus excludes", so its selector can only be RECOMMENDED
        #
        origin = wrapper["source"]["origin"]
        selector = wrapper["selection"]["managedDataIdentifierSelector"]
        if origin == "template" and selector != "RECOMMENDED":
            cls._fail(
                f"A wrapper from a template must use selector RECOMMENDED, not {selector}"
            )

    @classmethod
    def _validate_managed(cls, *, wrapper: dict) -> None:
        selection = wrapper["selection"]
        managed = wrapper["managedDataIdentifiers"]
        selector = selection["managedDataIdentifierSelector"]
        included = selection.get("managedDataIdentifierIds", [])
        excluded = selection.get("excludedManagedDataIdentifierIds", [])
        resolved = managed["resolved"]
        cls._no_duplicates(ids=resolved, what="managedDataIdentifiers.resolved")
        cls._no_duplicates(ids=included, what="selection.managedDataIdentifierIds")
        cls._no_duplicates(
            ids=excluded, what="selection.excludedManagedDataIdentifierIds"
        )
        overlap = set(resolved) & set(excluded)
        if overlap:
            cls._fail(
                f"Excluded managed data identifiers are resolved: {sorted(overlap)}"
            )
        recommended_list = managed.get("resolution", {}).get("recommended_list")
        if selector == "NONE":
            if resolved or included or excluded:
                cls._fail("Selector NONE cannot have managed data identifiers")
        elif selector == "INCLUDE":
            if not included:
                cls._fail("Selector INCLUDE needs managedDataIdentifierIds")
            if excluded:
                cls._fail("Selector INCLUDE cannot have excluded ids")
            if set(resolved) != set(included):
                cls._fail(
                    "Selector INCLUDE: resolved must be exactly managedDataIdentifierIds"
                )
        elif selector == "EXCLUDE":
            if not excluded:
                cls._fail("Selector EXCLUDE needs excludedManagedDataIdentifierIds")
            if included:
                cls._fail("Selector EXCLUDE cannot have managedDataIdentifierIds")
        elif selector == "ALL":
            if included or excluded:
                cls._fail("Selector ALL cannot have included or excluded ids")
        elif selector == "RECOMMENDED":
            if not recommended_list:
                cls._fail("Selector RECOMMENDED needs resolution.recommended_list")
            missing = set(included) - set(resolved)
            if missing:
                cls._fail(
                    f"Included managed data identifiers not resolved: {sorted(missing)}"
                )
        if selector != "RECOMMENDED" and recommended_list:
            cls._fail(f"Selector {selector} cannot have resolution.recommended_list")

    @classmethod
    def _validate_entries(
        cls, *, wrapper: dict, entries_key: str, selected_key: str, id_of
    ) -> None:
        #
        # selected ids and entries must match one to one: no selected id
        # without its definition, and no definition that is not selected
        #
        selected = wrapper["selection"].get(selected_key, [])
        cls._no_duplicates(ids=selected, what=f"selection.{selected_key}")
        entry_ids = [id_of(e) for e in wrapper.get(entries_key, [])]
        cls._no_duplicates(ids=entry_ids, what=entries_key)
        missing = set(selected) - set(entry_ids)
        if missing:
            cls._fail(
                f"Selected in {selected_key} but not in {entries_key}: {sorted(missing)}"
            )
        extra = set(entry_ids) - set(selected)
        if extra:
            cls._fail(
                f"In {entries_key} but not selected in {selected_key}: {sorted(extra)}"
            )

    @classmethod
    def _validate_allow_list_contents(cls, *, wrapper: dict) -> None:
        for allow_list in wrapper.get("allowLists", []):
            settings = allow_list["settings"]
            contents = allow_list.get("contents")
            name = settings["name"]
            if "s3WordsList" in settings["criteria"]:
                if contents is None:
                    cls._fail(f"Text allow list {name} has no contents")
                if contents["status"] == "OK":
                    if not contents["entries"]:
                        cls._fail(f"Allow list {name} has status OK but no entries")
                    if not contents.get("sha256"):
                        cls._fail(f"Allow list {name} has status OK but no sha256")
                elif contents["entries"]:
                    cls._fail(
                        f"Allow list {name} has status {contents['status']} but has entries"
                    )
            elif contents is not None:
                cls._fail(f"Regex allow list {name} cannot have contents")

    @classmethod
    def _no_duplicates(cls, *, ids: list, what: str) -> None:
        counts = Counter(ids)
        dups = sorted(i for i, n in counts.items() if n > 1)
        if dups:
            cls._fail(f"Duplicate ids in {what}: {dups}")
