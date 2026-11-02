import json
import logging
import os

from .macie_exceptions import MacieException
from .severity_levels import SeverityLevels


class ManagedCatalog:
    """our stand-ins for Macie's managed data identifiers, from a catalog
    file. The packaged catalog is csvpath/macie/rulesbase/
    managed_identifiers.json; a project rulesbase with user customizations
    may come later.

        catalog = ManagedCatalog.load()
        catalog.identifier(name="CREDIT_CARD_NUMBER")
        catalog.detector(name="credit_card")

    The file is checked when it is loaded, so a bad entry fails before any
    conversion or run."""

    DEFAULT = os.path.join(
        os.path.dirname(__file__), "rulesbase", "managed_identifiers.json"
    )
    VERSIONS = [1]
    KEYWORD_MODES = ["required", "absent", "none"]
    IDENTIFIER_KEYS = {
        "category",
        "detector",
        "keyword_mode",
        "keywords_from",
        "distance",
        "severity",
        "fidelity",
        "source",
        "retrieved",
    }

    def __init__(self, *, catalog: dict, path: str) -> None:
        self.path = path
        self.catalog = catalog

    @classmethod
    def logger(cls) -> logging.Logger:
        return logging.getLogger(cls.__name__)

    @classmethod
    def load(cls, *, path: str | None = None) -> "ManagedCatalog":
        path = cls.DEFAULT if path is None else path
        if not isinstance(path, str) or path.strip() == "":
            raise ValueError("path must be a non-empty str, or None for the default")
        try:
            with open(path, encoding="utf-8") as f:
                catalog = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            cls.logger().exception("Cannot read managed identifier catalog %s", path)
            raise MacieException(
                f"Cannot read managed identifier catalog {path}: {e}"
            ) from e
        cls.validate(catalog=catalog, path=path)
        return ManagedCatalog(catalog=catalog, path=path)

    @property
    def names(self) -> list[str]:
        return list(self.catalog["identifiers"].keys())

    def has(self, *, name: str) -> bool:
        return name in self.catalog["identifiers"]

    def identifier(self, *, name: str) -> dict:
        """the identifier's entry, with its keywords resolved from
        keyword_lists"""
        if not self.has(name=name):
            self._fail(f"No managed identifier {name!r} in {self.path}")
        entry = dict(self.catalog["identifiers"][name])
        entry["keywords"] = list(
            self.catalog["keyword_lists"][entry["keywords_from"]]["keywords"]
        )
        return entry

    def detector(self, *, name: str) -> dict:
        detectors = self.catalog["detectors"]
        if name not in detectors:
            self._fail(f"No detector {name!r} in {self.path}")
        return detectors[name]

    @classmethod
    def validate(cls, *, catalog: dict, path: str) -> None:
        if not isinstance(catalog, dict):
            cls._fail(f"Catalog {path} must be a JSON object")
        if catalog.get("version") not in cls.VERSIONS:
            cls._fail(
                f"Catalog {path} version {catalog.get('version')!r} is not supported"
            )
        for section in ["keyword_lists", "identifiers", "detectors"]:
            if not isinstance(catalog.get(section), dict):
                cls._fail(f"Catalog {path} needs a {section} object")
        for name, kl in catalog["keyword_lists"].items():
            words = kl.get("keywords") if isinstance(kl, dict) else None
            if not isinstance(words, list) or len(words) == 0:
                cls._fail(f"Keyword list {name} in {path} needs keywords")
            for w in words:
                if not isinstance(w, str) or w.strip() == "" or "|" in w or '"' in w:
                    cls._fail(f"Bad keyword {w!r} in keyword list {name} in {path}")
        for name, entry in catalog["identifiers"].items():
            cls._check_identifier(name=name, entry=entry, catalog=catalog, path=path)

    @classmethod
    def _check_identifier(cls, *, name: str, entry, catalog: dict, path: str) -> None:
        where = f"Managed identifier {name} in {path}"
        if not isinstance(entry, dict):
            cls._fail(f"{where} must be an object")
        missing = cls.IDENTIFIER_KEYS - set(entry)
        if missing:
            cls._fail(f"{where} is missing {', '.join(sorted(missing))}")
        if entry["keyword_mode"] not in cls.KEYWORD_MODES:
            cls._fail(f"{where} has keyword_mode {entry['keyword_mode']!r}")
        if entry["keywords_from"] not in catalog["keyword_lists"]:
            cls._fail(f"{where} names keyword list {entry['keywords_from']!r}")
        if entry["detector"] not in catalog["detectors"]:
            cls._fail(f"{where} names detector {entry['detector']!r}")
        d = entry["distance"]
        if not isinstance(d, int) or isinstance(d, bool) or not 1 <= d <= 300:
            cls._fail(f"{where} distance must be an int from 1 to 300, not {d!r}")
        try:
            SeverityLevels.parse(text=entry["severity"])
        except (MacieException, ValueError, TypeError) as e:
            cls._fail(f"{where} severity: {e}")

    @classmethod
    def _fail(cls, msg: str) -> None:
        cls.logger().error(msg)
        raise MacieException(msg)
