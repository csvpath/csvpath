import os
import re
from collections import Counter

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
# ("checks"): the spec folds them into the weights, not the read counts.
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
    def __init__(self, *, archive: str, files: str, csvpaths: str) -> None:
        if not archive or not files or not csvpaths:
            raise ValueError("archive, files and csvpaths roots are required")
        self.archive = os.path.abspath(archive)
        self.files = os.path.abspath(files)
        self.csvpaths = os.path.abspath(csvpaths)
        self.reads = Counter()
        self.checks = 0
        self.paths = []
        self._saved = {}

    @classmethod
    def for_csvpaths(cls, csvpaths) -> "ReadCounter":
        config = csvpaths.config
        return cls(
            archive=config.archive_path,
            files=config.inputs_files_path,
            csvpaths=config.inputs_csvpaths_path,
        )

    #
    # classifying a path
    #
    def read_kind(self, path: str) -> str | None:
        """the read kind of a file read at `path`, or None when the path is
        outside the three roots (config, logs and the like)."""
        path = os.path.abspath(str(path))
        name = os.path.basename(path)
        parent = os.path.dirname(path)
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
            if name.endswith(".log"):
                return "log"
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
        if path.startswith((self.archive, self.files, self.csvpaths)):
            return "other_listing"
        return None

    #
    # counting
    #
    def __enter__(self) -> "ReadCounter":
        counter = self
        real_open = open
        real_listdir = Nos.listdir
        real_exists = Nos.exists
        real_dir_exists = Nos.dir_exists
        real_isfile = Nos.isfile

        def counting_open(file, mode="r", *args, **kwargs):
            if "r" in mode and "+" not in mode:
                kind = counter.read_kind(file)
                if kind is not None:
                    counter.reads[kind] += 1
                    counter.paths.append((kind, str(file)))
            return real_open(file, mode, *args, **kwargs)

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
            "open": getattr(file_readers, "open", None),
            "listdir": real_listdir,
            "exists": real_exists,
            "dir_exists": real_dir_exists,
            "isfile": real_isfile,
        }
        file_readers.open = counting_open
        Nos.listdir = counting_listdir
        Nos.exists = checking(real_exists)
        Nos.dir_exists = checking(real_dir_exists)
        Nos.isfile = checking(real_isfile)
        return self

    def __exit__(self, *exc) -> None:
        if self._saved.get("open") is None:
            del file_readers.open
        else:
            file_readers.open = self._saved["open"]
        Nos.listdir = self._saved["listdir"]
        Nos.exists = self._saved["exists"]
        Nos.dir_exists = self._saved["dir_exists"]
        Nos.isfile = self._saved["isfile"]

    def total(self) -> int:
        return sum(self.reads.values())
