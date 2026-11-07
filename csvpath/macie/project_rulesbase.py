import logging
import os
import shutil

from .macie_exceptions import MacieException
from .managed_catalog import ManagedCatalog


class ProjectRulesbase:
    """finds a project's rulesbase for the managed identifier stand-ins
    (specs/macie/rulesbase-design.md, P1 and P3):

        <[macie] rulesbase, default rulesbase>/
          macie/
            managed_identifiers.json            the user's overrides
            packaged_managed_identifiers.json   our catalog, for reference

    The project opts in by creating the macie directory. Without it nothing
    is read or written and the packaged catalog is used as is, so a project
    that never customizes gets no new directories. With it, a load refreshes
    the reference copy, which is never read back, and merges the overrides
    file when there is one.

        catalog = ProjectRulesbase.catalog(config=config, refresh_reference=True)
    """

    SECTION = "macie"
    KEY = "rulesbase"
    DEFAULT = "rulesbase"
    SUBDIR = "macie"
    OVERRIDES = "managed_identifiers.json"
    REFERENCE = "packaged_managed_identifiers.json"
    #
    # the catalog a named-paths group was loaded with, in its assets; a
    # group run reads only this (rulesbase-design.md, P2)
    #
    CATALOG_ASSET = "macie_catalog.json"

    @classmethod
    def logger(cls) -> logging.Logger:
        return logging.getLogger(cls.__name__)

    @classmethod
    def directory(cls, *, config) -> str | None:
        """the macie directory of the project rulesbase, whether or not it
        exists; None without a config"""
        if config is None:
            return None
        v = config.get(section=cls.SECTION, name=cls.KEY, default=None)
        base = cls.DEFAULT if v is None or f"{v}".strip() == "" else f"{v}".strip()
        return os.path.join(base, cls.SUBDIR)

    @classmethod
    def catalog(cls, *, config, refresh_reference: bool = False) -> ManagedCatalog:
        """the packaged catalog with the project's overrides merged over it,
        or the packaged catalog when the project has no rulesbase"""
        if not isinstance(refresh_reference, bool):
            raise TypeError(
                f"refresh_reference must be a bool, not {type(refresh_reference)}"
            )
        d = cls.directory(config=config)
        if d is None or not os.path.isdir(d):
            return ManagedCatalog.load()
        if refresh_reference:
            cls._write_reference(directory=d)
        overrides = os.path.join(d, cls.OVERRIDES)
        if not os.path.exists(overrides):
            return ManagedCatalog.load()
        catalog = ManagedCatalog.load(overrides_path=overrides)
        cls.logger().info(
            "Macie: project rulesbase %s overrides %s",
            overrides,
            ", ".join(catalog.applied) or "nothing",
        )
        return catalog

    @classmethod
    def _write_reference(cls, *, directory: str) -> None:
        target = os.path.join(directory, cls.REFERENCE)
        try:
            shutil.copyfile(ManagedCatalog.DEFAULT, target)
        except OSError as e:
            cls.logger().exception("Cannot write %s", target)
            raise MacieException(
                f"Cannot write the reference catalog {target}: {e}"
            ) from e
