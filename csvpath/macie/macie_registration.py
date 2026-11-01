import logging
import os
from collections import Counter

from .macie_converter import MacieConverter
from .macie_exceptions import MacieException
from .macie_wrapper_loader import MacieWrapperLoader


class MacieRegistration:
    """what PathsManager needs to load a .macie.json wrapper as a
    named-paths group, kept here so the paths manager stays a few lines:

        paths, report = MacieRegistration.convert_file(path=p, config=config)

    and the one rule Macie adds to a group: a Macie csvpath's id is never
    shared with another csvpath in the group, since two csvpaths with one
    id would scan twice and blur whose findings are whose."""

    #
    # every csvpath MacieConverter writes has this metadata key
    #
    ORIGIN_KEY = "macie-origin"
    SECTION = "macie"

    @classmethod
    def logger(cls) -> logging.Logger:
        return logging.getLogger(cls.__name__)

    @classmethod
    def convert_file(cls, *, path: str, config) -> tuple[list[str], dict]:
        """the csvpath for a wrapper file, as a one-item list, and the
        conversion report as a dict"""
        if not isinstance(path, str) or path.strip() == "":
            raise ValueError("path must be a non-empty str")
        if not MacieWrapperLoader.is_wrapper_path(path=path):
            raise ValueError(f"Not a Macie wrapper file: {path}")
        wrapper = MacieWrapperLoader.from_path(path=path)
        converter = MacieConverter(wrapper=wrapper)
        conversion = converter.convert(
            name=cls.name_for(wrapper=wrapper, path=path), **cls.limits(config=config)
        )
        source = wrapper["source"]
        report = {
            "source_path": path,
            "name": conversion.name,
            "origin": source["origin"],
            "job_id": source.get("job_id"),
            "template_id": source.get("template_id"),
            "account_id": source.get("account_id"),
            "region": source.get("region"),
            "downloaded_at": source.get("downloaded_at"),
            "skipped": [
                {
                    "object": s.object,
                    "location": s.location,
                    "feature": s.feature,
                    "reason": s.reason,
                }
                for s in conversion.report.skipped
            ],
        }
        cls.logger().debug(
            "Converted Macie wrapper at %s, skipping %s items",
            path,
            len(report["skipped"]),
        )
        return ([conversion.csvpath.strip()], report)

    @classmethod
    def name_for(cls, *, wrapper: dict, path: str) -> str | None:
        """None, so the converter uses the job's or template's name, when
        that name can be a csvpath id. Otherwise the wrapper's file name,
        e.g. handcrafted_minimal for handcrafted_minimal.macie.json. The
        name doesn't change what is detected, so a fallback is safe."""
        aws = wrapper.get("aws") or {}
        source = aws.get("classificationJob") or aws.get(
            "sensitivityInspectionTemplate"
        )
        name = source.get("name") if source else None
        if isinstance(name, str) and MacieConverter.NAME.fullmatch(name):
            return None
        stem = os.path.basename(path)[: -len(MacieWrapperLoader.SUFFIX)]
        if MacieConverter.NAME.fullmatch(stem) is None:
            msg = (
                f"Cannot name the csvpath for {path}: the Macie name {name!r} and "
                f"the file name {stem!r} are not usable csvpath ids"
            )
            cls.logger().error(msg)
            raise MacieException(msg)
        return stem

    @classmethod
    def limits(cls, *, config) -> dict:
        """max_findings and max_detail from config.ini [macie], or the
        converter's defaults"""
        out = {}
        for key, default, minimum in [
            ("max_findings", MacieConverter.MAX_FINDINGS, 1),
            ("max_detail", MacieConverter.MAX_DETAIL, 0),
        ]:
            v = None
            if config is not None:
                v = config.get(section=cls.SECTION, name=key, default=None)
            if v is None or f"{v}".strip() == "":
                out[key] = default
                continue
            try:
                i = int(f"{v}".strip())
            except ValueError as e:
                cls.logger().exception("Bad [macie] %s: %r", key, v)
                raise MacieException(
                    f"config.ini [macie] {key} must be an int, not {v!r}"
                ) from e
            if i < minimum:
                raise MacieException(
                    f"config.ini [macie] {key} must be at least {minimum}, not {i}"
                )
            out[key] = i
        return out

    @classmethod
    def refuse_shared_ids(cls, *, group: str, paths: list[tuple[str, dict]]) -> None:
        """paths is every csvpath the group would hold, as (id, metadata).
        Raises if an id is used more than once and any csvpath using it is
        a Macie csvpath."""
        if not isinstance(paths, list):
            raise TypeError(f"paths must be a list, not {type(paths)}")
        counts = Counter(i for i, _ in paths if i is not None)
        for identity, n in counts.items():
            if n < 2:
                continue
            macie = [md for i, md in paths if i == identity and cls.ORIGIN_KEY in md]
            if len(macie) > 0:
                msg = (
                    f"Named-paths group {group} would have {n} csvpaths with the id "
                    f"{identity!r}, at least one from Macie. A Macie csvpath's id "
                    "must be unique in its group: rename one, or reload the group "
                    "without append"
                )
                cls.logger().error(msg)
                raise MacieException(msg)
