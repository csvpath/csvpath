import datetime
import json
import logging
import os

from .macie_exceptions import MacieException


class RecommendedLists:
    """the managed data identifier sets Macie recommends, which AWS
    publishes only in the Macie user guide, not through the API
    (specs/macie/download-design.md). Each is a dated asset in
    csvpath/macie/rulesbase/recommended/:

        jobs                         a job whose selector is RECOMMENDED
        automated_discovery          a sensitivity inspection template,
                                     for accounts that first enabled
                                     automated discovery on or after
                                     2023-08-02
        automated_discovery_static   the same, for accounts that first
                                     enabled it before 2023-08-02

    A wrapper records which list and which retrieval it used, e.g.
    jobs-recommended@2026-11-08, in managedDataIdentifiers.resolution.

        ids, label = RecommendedLists.for_job()
        ids, label = RecommendedLists.for_template(first_enabled_at=when)
    """

    DIR = os.path.join(os.path.dirname(__file__), "rulesbase", "recommended")
    JOBS = "jobs"
    AUTOMATED = "automated_discovery"
    AUTOMATED_STATIC = "automated_discovery_static"
    NAMES = [JOBS, AUTOMATED, AUTOMATED_STATIC]
    #
    # Macie: accounts that first enabled automated discovery before this
    # date keep the static set
    #
    DYNAMIC_FROM = datetime.datetime(2023, 8, 2, tzinfo=datetime.timezone.utc)

    @classmethod
    def logger(cls) -> logging.Logger:
        return logging.getLogger(cls.__name__)

    @classmethod
    def load(cls, *, name: str) -> dict:
        if name not in cls.NAMES:
            raise ValueError(f"name must be one of {cls.NAMES}, not {name!r}")
        path = os.path.join(cls.DIR, f"{name}.json")
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            cls.logger().exception("Cannot read recommended list %s", path)
            raise MacieException(f"Cannot read recommended list {path}: {e}") from e
        cls._check(data=data, path=path)
        return data

    @classmethod
    def label(cls, *, data: dict) -> str:
        """the list's name and the date we retrieved it from AWS"""
        return f"{data['name']}@{data['retrieved']}"

    @classmethod
    def for_job(cls) -> tuple[list[str], str]:
        data = cls.load(name=cls.JOBS)
        return list(data["ids"]), cls.label(data=data)

    @classmethod
    def for_template(
        cls, *, first_enabled_at: datetime.datetime
    ) -> tuple[list[str], str]:
        """the automated discovery set for an account, by when it first
        enabled automated discovery (GetAutomatedDiscoveryConfiguration
        firstEnabledAt)"""
        if not isinstance(first_enabled_at, datetime.datetime):
            raise TypeError(
                f"first_enabled_at must be a datetime, not {type(first_enabled_at)}"
            )
        if first_enabled_at.tzinfo is None:
            raise ValueError("first_enabled_at must be timezone aware")
        name = (
            cls.AUTOMATED
            if first_enabled_at >= cls.DYNAMIC_FROM
            else cls.AUTOMATED_STATIC
        )
        data = cls.load(name=name)
        return list(data["ids"]), cls.label(data=data)

    @classmethod
    def _check(cls, *, data, path: str) -> None:
        if not isinstance(data, dict):
            cls._fail(f"Recommended list {path} must be a JSON object")
        for key in ["name", "source", "retrieved"]:
            if not isinstance(data.get(key), str) or data[key].strip() == "":
                cls._fail(f"Recommended list {path} needs {key}")
        ids = data.get("ids")
        if not isinstance(ids, list) or len(ids) == 0:
            cls._fail(f"Recommended list {path} needs ids")
        if any(not isinstance(i, str) or i.strip() == "" for i in ids):
            cls._fail(f"Recommended list {path} has a bad id")
        if len(ids) != len(set(ids)):
            cls._fail(f"Recommended list {path} has duplicate ids")

    @classmethod
    def _fail(cls, msg: str) -> None:
        cls.logger().error(msg)
        raise MacieException(msg)
