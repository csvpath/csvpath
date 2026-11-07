import json
import logging
import os
from collections import Counter

from .macie_converter import MacieConverter
from .macie_exceptions import MacieException
from .macie_wrapper_loader import MacieWrapperLoader
from .project_rulesbase import ProjectRulesbase


class MacieGroupLoader:
    """the Macie side of loading a .macie.json wrapper into a named-paths
    group, kept here so the paths manager stays a few lines. (The wrapper
    file itself is read by MacieWrapperLoader.)

        paths, report, lists, catalog = MacieGroupLoader.convert_file(path=p, config=config)

    It also holds the one rule Macie adds to a group: a Macie csvpath's id
    is never shared with another csvpath in the group, since two csvpaths
    with one id would scan twice and blur whose findings are whose."""

    #
    # every csvpath MacieConverter writes has this metadata key
    #
    ORIGIN_KEY = "macie-origin"
    SECTION = "macie"
    CATALOG_ASSET = ProjectRulesbase.CATALOG_ASSET

    @classmethod
    def logger(cls) -> logging.Logger:
        return logging.getLogger(cls.__name__)

    @classmethod
    def convert_file(
        cls, *, path: str, config
    ) -> tuple[list[str], dict, dict[str, list[str]], dict]:
        """the csvpath for a wrapper file, as a one-item list, the
        conversion report as a dict, the text allow lists the csvpath
        loads, as {list name: entries}, and the managed identifier catalog
        it was converted with, the project rulesbase's overrides merged in.
        The report has each list's name and entry count, not its entries,
        and the overrides applied."""
        if not isinstance(path, str) or path.strip() == "":
            raise ValueError("path must be a non-empty str")
        if not MacieWrapperLoader.is_wrapper_path(path=path):
            raise ValueError(f"Not a Macie wrapper file: {path}")
        wrapper = MacieWrapperLoader.from_path(path=path)
        catalog = ProjectRulesbase.catalog(config=config, refresh_reference=True)
        converter = MacieConverter(wrapper=wrapper, catalog=catalog)
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
            "lists": [
                {"name": k, "entries": len(v)} for k, v in conversion.lists.items()
            ],
            "skipped": [
                {
                    "object": s.object,
                    "location": s.location,
                    "feature": s.feature,
                    "reason": s.reason,
                }
                for s in conversion.report.skipped
            ],
            "rulesbase": {
                "overrides_path": catalog.overrides_path,
                "applied": list(catalog.applied),
            },
        }
        cls.logger().debug(
            "Converted Macie wrapper at %s, skipping %s items",
            path,
            len(report["skipped"]),
        )
        return (
            [conversion.csvpath.strip()],
            report,
            dict(conversion.lists),
            catalog.catalog,
        )

    @classmethod
    def store_assets(
        cls,
        *,
        paths_manager,
        name: str,
        lists: dict[str, list[str]],
        catalog: dict,
        append: bool,
    ) -> None:
        """writes a wrapper's text allow lists and the managed identifier
        catalog it was converted with to the group's assets, creating the
        group if needed.

        When appending, a group whose catalog differs is refused before
        anything is written, as for lists: replacing it would change what
        the group's other Macie csvpaths detect. Reload the group without
        append to use a changed project rulesbase."""
        if paths_manager is None:
            raise ValueError("paths_manager cannot be None")
        if not isinstance(name, str) or name.strip() == "":
            raise ValueError("name must be a non-empty str")
        if not isinstance(catalog, dict):
            raise TypeError(f"catalog must be a dict, not {type(catalog)}")
        if not isinstance(append, bool):
            raise TypeError(f"append must be a bool, not {type(append)}")
        am = paths_manager.asset_manager
        if append is True and paths_manager.has_named_paths(name):
            have = am.get_asset_file(name, cls.CATALOG_ASSET)
            if have is not None and json.loads(have) != catalog:
                msg = (
                    f"Cannot append to named-paths group {name}: it was loaded with "
                    "a different managed identifier catalog (the packaged stand-ins "
                    "or the project rulesbase changed since). Appending would change "
                    "what the group's other Macie csvpaths detect. Reload the group "
                    "without append"
                )
                cls.logger().error(msg)
                raise MacieException(msg)
        cls.store_lists(
            paths_manager=paths_manager, name=name, lists=lists, append=append
        )
        am.store_asset_file(
            name=name,
            filename=cls.CATALOG_ASSET,
            contents=json.dumps(catalog, indent=2, ensure_ascii=False) + "\n",
        )

    @classmethod
    def store_lists(
        cls, *, paths_manager, name: str, lists: dict[str, list[str]], append: bool
    ) -> list[str]:
        """writes a wrapper's text allow lists to the group's assets, where
        load_list() reads them, creating the group if needed. Returns the
        list paths.

        When appending, a list already in the group with different entries
        is refused before anything is written: replacing it would change
        what an earlier csvpath in the group allows. The same entries are
        fine. Without append the group's csvpaths are replaced, so its lists
        are too."""
        if paths_manager is None:
            raise ValueError("paths_manager cannot be None")
        if not isinstance(name, str) or name.strip() == "":
            raise ValueError("name must be a non-empty str")
        if not isinstance(lists, dict):
            raise TypeError(f"lists must be a dict, not {type(lists)}")
        if not isinstance(append, bool):
            raise TypeError(f"append must be a bool, not {type(append)}")
        am = paths_manager.asset_manager
        for list_name in lists:
            am.check_list_name(list_name)
        if append is True and paths_manager.has_named_paths(name):
            for list_name, entries in lists.items():
                have = am.get_asset_file(name, f"{list_name}{am.LIST_SUFFIX}")
                if have is not None and have.splitlines() != list(entries):
                    msg = (
                        f"Cannot append to named-paths group {name}: its allow list "
                        f"{list_name!r} has different entries than the list with "
                        "that id in the new Macie wrapper. Replacing it would change "
                        "what the group's other csvpaths allow. Give the list a new "
                        "id, or reload the group without append"
                    )
                    cls.logger().error(msg)
                    raise MacieException(msg)
        paths_manager.configure_named_paths(name)
        return [
            am.store_list(name=name, list_name=k, values=list(v))
            for k, v in lists.items()
        ]

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
