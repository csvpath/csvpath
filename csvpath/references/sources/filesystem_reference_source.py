import json
import re

from csvpath.util.file_readers import DataFileReader
from csvpath.util.nos import Nos

from .reference_source import ReferenceSource


class FilesystemReferenceSource(ReferenceSource):
    """reads reference metadata from the JSON manifests and directories,
    through the managers, exactly as the finders did before sources
    existed. this is the default and the source of truth."""

    MANIFEST = "manifest.json"
    EXTRA_DATA = "_extra_data"

    @staticmethod
    def read_json(path: str):
        """a parsed JSON file, or None if it does not exist. never writes,
        unlike helpers that create a missing file."""
        if path is None or path == "":
            raise ValueError("Path cannot be None or empty")
        if not Nos(path).exists():
            return None
        with DataFileReader(path) as reader:
            return json.load(reader.source)

    #
    # FILES
    #
    def file_manifest(self, name: str) -> list:
        self._check_name(name, "Named-file name")
        return self.csvpaths.file_manager.get_manifest(name)

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
        manifest_path = Nos(archive).join(self.MANIFEST)
        if not Nos(manifest_path).exists():
            return []
        with DataFileReader(manifest_path) as reader:
            entries = json.load(reader.source)
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
        return self.read_json(Nos(run_dir).join(self.MANIFEST))

    def instance_manifest(self, instance_dir: str) -> dict | None:
        self._check_name(instance_dir, "Instance dir")
        return self.read_json(Nos(instance_dir).join(self.MANIFEST))

    def instance_dirs(self, run_dir: str) -> list[str]:
        self._check_name(run_dir, "Run dir")
        return [
            name
            for name in Nos(run_dir).listdir(dirs_only=True)
            if name != self.EXTRA_DATA
        ]
