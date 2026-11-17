import builtins
import os
import re
from collections import Counter

import csvpath.references.reference_finder_3 as reference_finder_3
import csvpath.util.file_readers as file_readers
from csvpath.util.nos import Nos

#
# The test oracle for cost estimates (references_v3_cost_estimates.md): it
# counts what a reference really reads on the local backend, by read kind, so
# an estimate can be checked against measured reads. It patches the two I/O
# seams every local read goes through -- the file readers' open() and Nos --
# rather than the reference sources, because run listings, content files and
# the existence checks happen outside the sources.
#
# Kinds follow the estimate's vocabulary. Existence checks are counted apart
# ("checks"): the spec folds them into the weights, not the read counts. A
# `:log(n)` tail is read by the reference finder's own open(), so that module
# is patched too, and the configured log file is a fourth root. A recursive
# listing counts as one listing (no reference recurses today). `sql_query`
# is outside this oracle: it counts local I/O only.
#
# The patches are process-global, so use it in one thread at a time.
#
RUN_DIR_NAME = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}(_\d+)?$")

CONTENT = {
    "errors.json": "errors_json",
    "vars.json": "vars_json",
    "meta.json": "meta_json",
    "definition.json": "definition",
    "README.md": "readme",
}


class ReadCounter:
    PATCHED_OPENS = (file_readers, reference_finder_3)

    def __init__(
        self, *, archive: str, files: str, csvpaths: str, log_file: str | None = None
    ) -> None:
        if not archive or not files or not csvpaths:
            raise ValueError("archive, files and csvpaths roots are required")
        self.archive = os.path.abspath(archive)
        self.files = os.path.abspath(files)
        self.csvpaths = os.path.abspath(csvpaths)
        self.log_file = os.path.abspath(log_file) if log_file else None
        self.reads = Counter()
        self.checks = 0
        self.paths = []
        self._saved = {}

    @classmethod
    def for_csvpaths(cls, csvpaths) -> "ReadCounter":
        if csvpaths is None:
            raise ValueError("csvpaths cannot be None")
        config = csvpaths.config
        return cls(
            archive=config.archive_path,
            files=config.inputs_files_path,
            csvpaths=config.inputs_csvpaths_path,
            log_file=config.log_file,
        )

    #
    # classifying a path
    #
    def read_kind(self, path: str) -> str | None:
        """the read kind of a file read at `path`, or None when the path is
        outside the four roots (the archive, the named-files and named-paths
        homes, and the log file): config files and the like."""
        path = os.path.abspath(str(path))
        name = os.path.basename(path)
        parent = os.path.dirname(path)
        if self.log_file is not None and path == self.log_file:
            return "log"
        for root in (self.archive, self.files, self.csvpaths):
            if path == os.path.join(root, "manifest.json"):
                return "ledger"
        if path.startswith(self.files + os.sep):
            if name == "manifest.json":
                return "named_file_manifest"
            return CONTENT.get(name, "version_file")
        if path.startswith(self.csvpaths + os.sep):
            if name == "manifest.json":
                return "group_manifest"
            return CONTENT.get(name, "version_file")
        if path.startswith(self.archive + os.sep):
            if name == "manifest.json":
                if RUN_DIR_NAME.match(os.path.basename(parent)):
                    return "run_manifest"
                return "instance_manifest"
            return CONTENT.get(name, "data_file")
        return None

    def listing_kind(self, path: str) -> str | None:
        path = os.path.abspath(str(path))
        if path in (self.files, self.csvpaths):
            return "name_listing"
        if path.startswith(self.archive + os.sep) and RUN_DIR_NAME.match(
            os.path.basename(path)
        ):
            return "run_listing"
        for root in (self.archive, self.files, self.csvpaths):
            if path == root or path.startswith(root + os.sep):
                return "other_listing"
        return None

    #
    # counting
    #
    def __enter__(self) -> "ReadCounter":
        counter = self
        real_listdir = Nos.listdir
        real_exists = Nos.exists
        real_dir_exists = Nos.dir_exists
        real_isfile = Nos.isfile

        def counting(real_open):
            def counting_open(file, mode="r", *args, **kwargs):
                if "r" in mode and "+" not in mode:
                    kind = counter.read_kind(file)
                    if kind is not None:
                        counter.reads[kind] += 1
                        counter.paths.append((kind, str(file)))
                return real_open(file, mode, *args, **kwargs)

            return counting_open

        def counting_listdir(nos, **kwargs):
            kind = counter.listing_kind(nos.path)
            if kind is not None:
                counter.reads[kind] += 1
                counter.paths.append((kind, str(nos.path)))
            return real_listdir(nos, **kwargs)

        def checking(real):
            def check(nos):
                if counter.read_kind(nos.path) or counter.listing_kind(nos.path):
                    counter.checks += 1
                return real(nos)

            return check

        self._saved = {
            "opens": [(m, m.__dict__.get("open")) for m in self.PATCHED_OPENS],
            "listdir": real_listdir,
            "exists": real_exists,
            "dir_exists": real_dir_exists,
            "isfile": real_isfile,
        }
        for module in self.PATCHED_OPENS:
            # wrap whatever open the module sees now, so counters nest
            module.open = counting(module.__dict__.get("open", builtins.open))
        Nos.listdir = counting_listdir
        Nos.exists = checking(real_exists)
        Nos.dir_exists = checking(real_dir_exists)
        Nos.isfile = checking(real_isfile)
        return self

    def __exit__(self, *exc) -> None:
        for module, saved in self._saved["opens"]:
            if saved is None:
                del module.open
            else:
                module.open = saved
        Nos.listdir = self._saved["listdir"]
        Nos.exists = self._saved["exists"]
        Nos.dir_exists = self._saved["dir_exists"]
        Nos.isfile = self._saved["isfile"]

    def total(self) -> int:
        return sum(self.reads.values())
