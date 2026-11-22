import json
import re

from csvpath.util.file_readers import DataFileReader
from csvpath.util.nos import Nos

from ..reference_exceptions_3 import ReferenceRuntimeException3
from .reference_source import ReferenceSource


class FilesystemReferenceSource(ReferenceSource):
    """reads reference metadata from the JSON manifests and directories,
    through the managers, exactly as the finders did before sources
    existed. this is the default and the source of truth."""

    MANIFEST = "manifest.json"
    EXTRA_DATA = "_extra_data"

    @staticmethod
    def read_json(*, path: str, logger=None):
        """a parsed JSON file, or None if it does not exist. never writes,
        unlike helpers that create a missing file. A file that is not valid
        JSON raises, naming it; it raised a bare JSONDecodeError with no path
        (reviewer on #649; fail fast). The raise is a
        ReferenceRuntimeException3, logged when a logger is given: the
        reference is fine, the framework data is not (A19, decision D24)."""
        if path is None or path == "":
            raise ValueError("Path cannot be None or empty")
        if not Nos(path).exists():
            return None
        with DataFileReader(path) as reader:
            try:
                return json.load(reader.source)
            except json.JSONDecodeError as e:
                msg = f"{path} is not valid JSON: {e}"
                if logger is not None:
                    logger.error(msg)
                raise ReferenceRuntimeException3(msg) from e

    #
    # FILES
    #
    def file_manifest(self, name: str) -> list:
        self._check_name(name, "Named-file name")
        #
        # a named-file with no manifest (never registered, or deleted) has
        # no versions: [], as paths_manifest() gives for a missing group.
        # "A reference query that doesn't find results does not raise"
        # (David, 2026-11-22, D40 f; 5.3). FileManager.get_manifest()
        # raises ValueError for it; only when the manifest file is really
        # absent is that "no versions" -- any other ValueError (a manifest
        # that is not a list) is re-raised.
        #
        try:
            return self.csvpaths.file_manager.get_manifest(name)
        except ValueError:
            home = self.csvpaths.file_manager.named_file_home(name)
            if Nos(Nos(home).join("manifest.json")).exists():
                raise
            return []

    def files_ledger(self) -> list | None:
        return self.csvpaths.file_manager.files_root_manifest

    def file_names(self) -> list[str]:
        #
        # sorted: a directory listing has no order to rely on, and the SQL
        # source returns the same order
        #
        return sorted(self.csvpaths.file_manager.named_file_names)

    #
    # CSVPATHS
    #
    def paths_manifest(self, name: str) -> list:
        self._check_name(name, "Named-paths name")
        return self.csvpaths.paths_manager.get_manifest_for_name(name)

    def paths_ledger(self) -> list:
        return self.csvpaths.paths_manager.paths_root_manifest

    def paths_names(self) -> list[str]:
        #
        # sorted, as file_names
        #
        return sorted(self.csvpaths.paths_manager.named_paths_names)

    #
    # RESULTS
    #
    def results_ledger(self) -> list:
        return self.csvpaths.results_manager.results_root_manifest

    def run_homes(
        self, *, root_major: str | None, name_filter: str | None
    ) -> list[tuple[str, str]]:
        #
        # read from the archive-root manifest.json rather than by walking
        # directories, so a group's template depth does not matter. many
        # entries share a run_home (one per csvpath statement), so dedupe;
        # a stale entry (the run since deleted) is dropped by the
        # existence check. see ResultsReferenceFinder3's module docstring.
        #
        archive = self.csvpaths.config.get(section="results", name="archive")
        # read_json() names the file if it is not valid JSON (reviewer on
        # #653: this read raised a bare JSONDecodeError)
        entries = self.read_json(
            path=Nos(archive).join(self.MANIFEST), logger=self._logger
        )
        if entries is None:
            return []
        return self._run_homes_from(
            entries=entries,
            root_major=root_major,
            name_filter=name_filter,
            logger=self._logger,
        )

    @property
    def _logger(self):
        return getattr(self.csvpaths, "logger", None)

    @staticmethod
    def _run_homes_from(
        *, entries: list, root_major: str | None, name_filter: str | None, logger=None
    ) -> list[tuple[str, str]]:
        """the distinct, still-existing (run_home, named_paths_name) pairs
        in archive ledger entries, in ledger order. shared with the SQL
        source, which passes the same entries from its mirror. An entry with
        no uuid raises, logged when a logger is given: there should be none
        (David, 2026-10-31), as every FILES, CSVPATHS and RESULTS ledger read
        checks (decisions D20, D21). A ReferenceRuntimeException3, as for an
        unparseable file (A19, decision D24)."""
        if entries is None or not isinstance(entries, list):
            raise TypeError("Entries must be a list")
        for entry in entries:
            if not entry.get("uuid"):
                msg = f"A results ledger entry has no uuid: {entry}"
                if logger is not None:
                    logger.error(msg)
                raise ReferenceRuntimeException3(msg)
        homes = []
        seen = set()
        for entry in entries:
            group = entry.get("named_paths_name")
            if root_major is not None and group != root_major:
                continue
            if name_filter is not None and not re.search(name_filter, group or ""):
                continue
            run_home = entry.get("run_home")
            if run_home and run_home not in seen:
                seen.add(run_home)
                homes.append((run_home, group))
        return [pair for pair in homes if Nos(pair[0]).exists()]

    def run_manifest(self, run_dir: str) -> dict | None:
        self._check_name(run_dir, "Run dir")
        return self.read_json(
            path=Nos(run_dir).join(self.MANIFEST), logger=self._logger
        )

    def instance_manifest(self, instance_dir: str) -> dict | None:
        self._check_name(instance_dir, "Instance dir")
        return self.read_json(
            path=Nos(instance_dir).join(self.MANIFEST), logger=self._logger
        )

    def instance_dirs(self, run_dir: str) -> list[str]:
        self._check_name(run_dir, "Run dir")
        return [
            name
            for name in Nos(run_dir).listdir(dirs_only=True)
            if name != self.EXTRA_DATA
        ]
