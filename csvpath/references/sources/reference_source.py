from abc import ABC, abstractmethod


class ReferenceSource(ABC):
    """the metadata the v3 reference finders select from: manifests,
    root ledgers, names, run homes and instance directories. the finders
    delegate every such read to a source, so where the metadata comes
    from (the filesystem; SQL when [references] sql = on; both, compared,
    when shadow) is not their concern.

    real data reads -- data files, errors.json, vars.json, definition.json,
    readmes, logs, and a bare :manifest()'s raw bytes -- are not part of
    a source. they always come from the filesystem.
    """

    def __init__(self, *, csvpaths) -> None:
        if csvpaths is None:
            raise ValueError("CsvPaths cannot be None")
        self._csvpaths = csvpaths

    @property
    def csvpaths(self):
        return self._csvpaths

    @staticmethod
    def _check_name(name: str, what: str) -> None:
        if name is None:
            raise ValueError(f"{what} cannot be None")
        if not isinstance(name, str):
            raise TypeError(f"{what} must be a str, not {type(name).__name__}")
        if name.strip() == "":
            raise ValueError(f"{what} cannot be empty")

    #
    # FILES
    #
    @abstractmethod
    def file_manifest(self, name: str) -> list:
        """the named-file's own manifest, in registration order"""

    @abstractmethod
    def files_ledger(self) -> list | None:
        """the named-files root ledger, including failed registrations.
        None if nothing has been registered yet."""

    @abstractmethod
    def file_names(self) -> list[str]:
        """every named-file name, sorted"""

    #
    # CSVPATHS
    #
    @abstractmethod
    def paths_manifest(self, name: str) -> list:
        """the named-paths group's own manifest, in load order"""

    @abstractmethod
    def paths_ledger(self) -> list:
        """the named-paths root ledger"""

    @abstractmethod
    def paths_names(self) -> list[str]:
        """every named-paths group name, sorted"""

    #
    # RESULTS
    #
    @abstractmethod
    def results_ledger(self) -> list:
        """the archive-root run ledger"""

    @abstractmethod
    def run_homes(
        self, *, root_major: str | None, name_filter: str | None
    ) -> list[tuple[str, str]]:
        """every distinct, still-existing (run_home, named_paths_name)
        pair, in ledger order. root_major limits it to one group;
        name_filter is a regex checked against each group name."""

    @abstractmethod
    def run_manifest(self, run_dir: str) -> dict | None:
        """a run's own manifest. None if it does not exist."""

    @abstractmethod
    def instance_manifest(self, instance_dir: str) -> dict | None:
        """an instance's own manifest. None if it does not exist."""

    @abstractmethod
    def instance_dirs(self, run_dir: str) -> list[str]:
        """the names of a run's instance directories, in no particular
        order"""
