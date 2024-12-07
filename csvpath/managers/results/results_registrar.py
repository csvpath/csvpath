import os
from pathlib import Path
from datetime import datetime, timezone
import json
import time
import hashlib
from .result import Result
from .result_serializer import ResultSerializer
from .result_registrar import ResultRegistrar
from .results_metadata import ResultsMetadata
from ..run.run_metadata import RunMetadata
from ..registrar import Registrar
from ..listener import Listener
from ..metadata import Metadata
from csvpath.util.exceptions import FileException


class ResultsRegistrar(Registrar, Listener):
    def __init__(
        self, *, csvpaths, run_dir: str, pathsname: str, results: list[Result] = None
    ) -> None:
        super().__init__(csvpaths)
        self.pathsname = pathsname
        self.run_dir = run_dir
        self.results = results
        self.load_additional_listeners("results")

    def register_start(self, mdata: ResultsMetadata) -> None:
        mdata.status = "start"
        mdata.manifest_path = self.manifest_path
        filename = mdata.named_file_name
        fingerprint = self.csvpaths.file_manager.get_fingerprint_for_name(filename)
        filepath = self.csvpaths.file_manager.get_named_file(filename)
        ffingerprint = self._fingerprint_file(filepath)
        mdata.named_file_fingerprint = ffingerprint
        if self.results and len(self.results) > 0:
            mdata.by_line = self.results[0].by_line
        mdata.named_file_fingerprint_on_file = fingerprint
        mdata.named_file_path = filepath
        mdata.named_file_size = self._size(filepath)
        mdata.named_file_last_change = self._last_change(filepath)
        self.distribute_update(mdata)
        # after we distribute the update
        # if we see a fingerprint mismatch we need to log it
        # and maybe blow up
        if mdata.named_file_fingerprint and mdata.named_file_fingerprint_on_file:
            if mdata.named_file_fingerprint != mdata.named_file_fingerprint_on_file:
                self.csvpaths.logger.warning(
                    "fingerprints of input file %s do not agree: orig:%s != current:%s",
                    mdata.named_file_path,
                    mdata.named_file_fingerprint,
                    mdata.named_file_fingerprint_on_file,
                )
            houf = self.csvpaths.config.halt_on_unmatched_file_fingerprints()
            if (
                houf is True
                and mdata.named_file_fingerprint != mdata.named_file_fingerprint_on_file
            ):
                raise FileException(
                    f"""File was modified since being registered.
                    New {mdata.named_file_fingerprint} does not equal
                    on-file {mdata.named_file_fingerprint_on_file}.
                    See manifest for {mdata.named_file_path} at {mdata.time}.
                    Processing halted."""
                )

    def register_complete(self, mdata) -> None:
        #
        # load what's already in the manifest
        #
        m = self.manifest
        mdata.from_manifest(m)
        if self.results and len(self.results) > 0:
            mdata.by_line = self.results[0].by_line
        mdata.set_time_completed()
        mdata.status = "complete"
        mdata.all_completed = self.all_completed()
        mdata.all_valid = self.all_valid()
        mdata.error_count = self.error_count()
        mdata.all_expected_files = self.all_expected_files()
        mdata.manifest_path = self.manifest_path
        self.distribute_update(mdata)

    def metadata_update(self, mdata: Metadata) -> None:
        m = {}
        m["time"] = mdata.time_string
        m["uuid"] = mdata.uuid_string
        m["serial"] = mdata.by_line is False
        if mdata.time_completed:
            m["time_completed"] = mdata.time_completed_string
            m["all_completed"] = mdata.all_completed
            m["all_valid"] = mdata.all_valid
            m["error_count"] = mdata.error_count
            m["all_expected_files"] = mdata.all_expected_files
        m["status"] = mdata.status
        m["run_home"] = mdata.run_home
        m["named_results_name"] = mdata.named_results_name
        m["named_paths_name"] = mdata.named_paths_name
        m["named_file_name"] = mdata.named_file_name
        m["named_file_path"] = mdata.named_file_path
        m["named_file_size"] = mdata.named_file_size
        m["named_file_last_change"] = mdata.named_file_last_change
        m["named_file_fingerprint"] = mdata.named_file_fingerprint
        m["named_file_fingerprint_on_file"] = mdata.named_file_fingerprint_on_file
        mp = mdata.manifest_path
        m["manifest_path"] = mp
        with open(mp, "w", encoding="utf-8") as file:
            json.dump(m, file, indent=2)

    def _fingerprint_file(self, path) -> str:
        with open(path, "rb") as f:
            h = hashlib.file_digest(f, hashlib.sha256)
            h = h.hexdigest()
        return h

    def _size(self, path) -> str:
        try:
            return os.stat(path).st_size
        except FileNotFoundError:
            return 0

    def _last_change(self, path) -> str:
        try:
            last_mod = os.stat(path).st_mtime
            last_mod = time.ctime(last_mod)
            return last_mod
        except FileNotFoundError:
            return -1

    def all_valid(self) -> bool:
        for r in self.results:
            if not r.csvpath.is_valid:
                return False
        return True

    def all_completed(self) -> bool:
        for r in self.results:
            if not r.csvpath.completed:
                return False
        return True

    def error_count(self) -> bool:
        ec = 0
        for r in self.results:
            ec += r.errors_count
        return ec

    def all_expected_files(self) -> bool:
        rs = ResultSerializer(self.csvpaths.config.archive_path)
        for r in self.results:
            rr = ResultRegistrar(csvpaths=self.csvpaths, result=r, result_serializer=rs)
            if not rr.all_expected_files:
                return False
        return True

    @property
    def manifest(self) -> dict[str, str | bool]:
        mp = self.manifest_path
        with open(mp, "r", encoding="utf-8") as file:
            d = json.load(file)
            return d
        return None

    @property
    def manifest_path(self) -> str:
        if not os.path.exists(self.run_dir):
            Path(self.run_dir).mkdir(parents=True, exist_ok=True)
        mp = os.path.join(self.run_dir, "manifest.json")
        return mp
