import copy
import json
import logging

from .macie_exceptions import MacieException


class RulesbaseOverrides:
    """merges a project's overrides of the managed identifier stand-ins
    over the packaged catalog (specs/macie/rulesbase-design.md, P1). The
    overrides file holds only the user's changes, so new identifiers and
    fixes in later releases still arrive:

        {
          "version": 1,
          "keyword_lists": { "br_rg": { "keywords": ["registro geral"],
                                        "why": "rg matches our cargo column" } },
          "identifiers": { "LATITUDE_LONGITUDE": { "severity": "1:MEDIUM 2:HIGH" } },
          "detectors": { "br_rg": { "formats": ["##.###.###-[0-9X]"] } }
        }

    The rules, each refused loudly when broken:

        keyword_lists   an entry replaces the named fields of the packaged
                        list of that name, or adds a new list, which must
                        have keywords
        identifiers     only identifiers in the packaged catalog; only the
                        keys in IDENTIFIER_KEYS. Macie's category and our
                        choice of detector are not overridable
        detectors       only detectors in the packaged catalog; only the
                        keys the detector's class reads (its CONFIG_KEYS)

    Every entry may have a "why", the user's note, kept in the merged
    catalog. The merged catalog is checked by ManagedCatalog.validate(), and
    every overridden detector is built once, so a bad format fails here,
    not in a run."""

    VERSIONS = [1]
    SECTIONS = ["keyword_lists", "identifiers", "detectors"]
    TOP_KEYS = {"version", "notes", *SECTIONS}
    NOTE_KEY = "why"
    KEYWORD_LIST_KEYS = {"keywords"}
    IDENTIFIER_KEYS = {
        "keyword_mode",
        "keywords_from",
        "distance",
        "severity",
        "partial",
    }

    @classmethod
    def logger(cls) -> logging.Logger:
        return logging.getLogger(cls.__name__)

    @classmethod
    def read(cls, *, path: str) -> dict:
        if not isinstance(path, str) or path.strip() == "":
            raise ValueError("path must be a non-empty str")
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            cls.logger().exception("Cannot read project rulesbase %s", path)
            raise MacieException(f"Cannot read project rulesbase {path}: {e}") from e

    @classmethod
    def merge(cls, *, base: dict, overrides: dict, path: str) -> tuple[dict, list[str]]:
        """the merged catalog, and the overrides applied as section.name
        strings, e.g. ["keyword_lists.br_rg"]. base is not changed."""
        if not isinstance(base, dict):
            raise TypeError(f"base must be a dict, not {type(base)}")
        if not isinstance(path, str) or path.strip() == "":
            raise ValueError("path must be a non-empty str")
        where = f"Project rulesbase {path}"
        if not isinstance(overrides, dict):
            cls._fail(f"{where} must be a JSON object")
        if overrides.get("version") not in cls.VERSIONS:
            cls._fail(f"{where} version {overrides.get('version')!r} is not supported")
        unknown = set(overrides) - cls.TOP_KEYS
        if unknown:
            cls._fail(f"{where} has unknown sections: {', '.join(sorted(unknown))}")
        merged = copy.deepcopy(base)
        applied = []
        for section in cls.SECTIONS:
            entries = overrides.get(section, {})
            if not isinstance(entries, dict):
                cls._fail(f"{where} {section} must be an object")
            for name, entry in entries.items():
                cls._merge_entry(
                    merged=merged, section=section, name=name, entry=entry, where=where
                )
                applied.append(f"{section}.{name}")
        return merged, applied

    @classmethod
    def _merge_entry(
        cls, *, merged: dict, section: str, name: str, entry, where: str
    ) -> None:
        at = f"{where} {section}.{name}"
        if not isinstance(entry, dict) or len(entry) == 0:
            cls._fail(f"{at} must be a non-empty object")
        why = entry.get(cls.NOTE_KEY)
        if why is not None and (not isinstance(why, str) or why.strip() == ""):
            cls._fail(f"{at} {cls.NOTE_KEY} must be a non-empty str when present")
        existing = merged[section].get(name)
        allowed = cls._allowed_keys(
            section=section, name=name, existing=existing, at=at
        )
        bad = set(entry) - allowed - {cls.NOTE_KEY}
        if bad:
            cls._fail(
                f"{at} cannot override {', '.join(sorted(bad))}; "
                f"it can override {', '.join(sorted(allowed))}"
            )
        if existing is None:
            merged[section][name] = dict(entry)
        else:
            existing.update(entry)

    @classmethod
    def _allowed_keys(cls, *, section: str, name: str, existing, at: str) -> set:
        if section == "keyword_lists":
            return cls.KEYWORD_LIST_KEYS
        if existing is None:
            cls._fail(
                f"{at} is not in the packaged catalog; a project rulesbase can "
                f"change {section}, not add them"
            )
        if section == "identifiers":
            return cls.IDENTIFIER_KEYS
        #
        # imported here: the detectors package is large, and the catalog is
        # loaded without it when nothing is overridden
        #
        from .detectors import DETECTORS

        return set(DETECTORS[name].CONFIG_KEYS)

    @classmethod
    def check_detectors(cls, *, catalog: dict, applied: list[str], path: str) -> None:
        """builds each overridden detector, through every identifier that
        uses it, so its own checks run (formats compile, lists are lists).
        Identifiers whose overrides change only keywords or severity build
        nothing here."""
        from .detectors import DETECTORS
        from .managed_catalog import ManagedCatalog

        overridden = {a.split(".", 1)[1] for a in applied if a.startswith("detectors.")}
        for ident, entry in catalog["identifiers"].items():
            base, parameter = ManagedCatalog.detector_parts(detector=entry["detector"])
            if base not in overridden:
                continue
            config = catalog["detectors"][base]
            try:
                if getattr(DETECTORS[base], "TAKES_PARAMETER", False):
                    DETECTORS[base](config=config, parameter=parameter)
                else:
                    DETECTORS[base](config=config)
            except (MacieException, ValueError, TypeError) as e:
                cls._fail(
                    f"Project rulesbase {path} detectors.{base} (for {ident}): {e}"
                )

    @classmethod
    def _fail(cls, msg: str) -> None:
        cls.logger().error(msg)
        raise MacieException(msg)
