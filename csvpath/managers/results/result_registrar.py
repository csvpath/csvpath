import os
import json
import hashlib
from pathlib import Path

from datetime import datetime
from ..listener import Listener
from ..metadata import Metadata
from ..registrar import Registrar
from .result_metadata import ResultMetadata


class ResultRegistrar(Registrar, Listener):
    def __init__(self, *, csvpaths, result, result_serializer=None):
        super().__init__(csvpaths)
        self.result = result
        self.result_serializer = result_serializer
        self.load_additional_listeners("result")

    def register_start(self, mdata: Metadata) -> None:
        p = self.named_paths_manifest
        mdata.by_line = self.result.by_line
        mdata.instance_index = self.result.run_index
        mdata.actual_data_file = self.result.actual_data_file
        mdata.origin_data_file = self.result.origin_data_file
        ri = int(self.result.run_index) if self.result.run_index else 0
        if ri >= 1:
            rs = self.result.csvpath.csvpaths.results_manager.get_named_results(
                self.result.paths_name
            )
            r = rs[ri - 1]
            mdata.preceding_instance_identity = r.identity_or_index
        if p is None:
            self.result.csvpath.csvpaths.logger.debug(
                "No named-paths manifest available at %s so not setting named_paths_uuid_string",
                self.named_paths_manifest_path,
            )
        else:
            mdata.named_paths_uuid_string = p["uuid"]
        self.distribute_update(mdata)

    def register_complete(self, mdata: Metadata = None) -> None:
        #
        # results manager delegates the bits to the
        # serializer and the metadata assembly to this
        # registrar, so we expect it to hand us nothing
        # but the result object and serializer.
        #
        m = self.manifest
        if mdata is None:
            mdata = ResultMetadata(config=self.csvpaths.config)
        mdata.from_manifest(m)
        mdata.archive_name = self.archive_name
        mdata.named_results_name = self.result.paths_name
        mdata.run = self.result_serializer.get_run_dir_name_from_datetime(
            self.result.run_time
        )
        mdata.by_line = self.result.by_line
        mdata.source_mode_preceding = self.result.source_mode_preceding
        mdata.run_home = self.result.run_dir
        mdata.instance_home = self.result.instance_dir
        mdata.instance_identity = self.result.identity_or_index
        mdata.instance_index = self.result.run_index
        mdata.named_file_name = self.result.file_name
        mdata.input_data_file = self.result.file_name
        mdata.file_fingerprints = self.file_fingerprints
        mdata.file_count = len(mdata.file_fingerprints)
        mdata.error_count = self.result.errors_count
        mdata.valid = self.result.csvpath.is_valid
        mdata.completed = self.completed
        mdata.files_expected = self.all_expected_files
        if self.result.csvpath.transfers:
            tpaths = self.result.csvpath.csvpaths.results_manager.transfer_paths(
                self.result
            )
            mdata.transfers = tpaths
        mdata.actual_data_file = self.result.actual_data_file
        mdata.origin_data_file = self.result.origin_data_file
        ri = int(self.result.run_index) if self.result.run_index else 0
        if ri >= 1:
            rs = self.result.csvpath.csvpaths.results_manager.get_named_results(
                self.result.paths_name
            )
            r = rs[ri - 1]
            mdata.preceding_instance_identity = r.identity_or_index
        self.distribute_update(mdata)

    def metadata_update(self, mdata: Metadata) -> None:
        m = {}
        if mdata.time is None:
            raise ValueError("Time cannot be None")
        m["time"] = mdata.time_string
        m["uuid"] = mdata.uuid_string
        m["serial"] = mdata.by_line is False
        m["archive_name"] = mdata.archive_name
        m["named_results_name"] = mdata.named_results_name
        m["named_paths_uuid"] = mdata.named_paths_uuid_string
        m["run"] = mdata.run
        m["run_home"] = mdata.run_home
        m["instance_identity"] = mdata.instance_identity
        m["instance_index"] = mdata.instance_index
        m["instance_home"] = mdata.instance_home
        m["file_fingerprints"] = mdata.file_fingerprints
        m["files_expected"] = mdata.files_expected
        m["file_count"] = mdata.file_count
        m["valid"] = mdata.valid
        m["completed"] = mdata.completed
        m["source_mode_preceding"] = mdata.source_mode_preceding
        if mdata.source_mode_preceding:
            m["preceding_instance_identity"] = mdata.preceding_instance_identity
        m["actual_data_file"] = mdata.actual_data_file
        m["origin_data_file"] = mdata.origin_data_file
        m["named_file_name"] = mdata.named_file_name
        if mdata.transfers:
            m["transfers"] = mdata.transfers
        mp = self.manifest_path
        m["manifest_path"] = mp
        with open(mp, "w", encoding="utf-8") as file:
            json.dump(m, file, indent=2)

    @property
    def archive_name(self) -> str:
        ap = self.result.csvpath.config.archive_path
        i = ap.rfind(os.sep)
        if i > 0:
            return ap[i + 1 :]
        return ap

    # gets the manifest for the named_paths as a whole
    @property
    def named_paths_manifest(self) -> dict | None:
        if os.path.exists(self.named_paths_manifest_path):
            with open(self.named_paths_manifest_path, "r", encoding="utf-8") as file:
                d = json.load(file)
                return d
        return None

    # gets the manifest for the named_paths as a whole from the run dir
    @property
    def named_paths_manifest_path(self) -> str:
        return os.path.join(self.result.run_dir, "manifest.json")

    @property
    def manifest(self) -> dict | None:
        mp = self.manifest_path
        if not os.path.exists(mp):
            with open(self.manifest_path, "w", encoding="utf-8") as file:
                json.dump({}, file, indent=2)
                return {}
        with open(self.manifest_path, "r", encoding="utf-8") as file:
            d = json.load(file)
            return d
        return None

    @property
    def manifest_path(self) -> str:
        h = os.path.join(self.result_path, "manifest.json")
        return h

    @property
    def result_path(self) -> str:
        rdir = self.result_serializer.get_instance_dir(
            run_dir=self.result.run_dir, identity=self.result.identity_or_index
        )
        if not os.path.exists(rdir):
            Path(rdir).mkdir(parents=True, exist_ok=True)
        return rdir

    @property
    def completed(self) -> bool:
        return self.result.csvpath.completed

    @property
    def all_expected_files(self) -> bool:
        #
        # we can not have data.csv, unmatched.csv, and printouts.txt without it
        # necessarily being a failure mode. but we can require them as a matter
        # of content validation.
        #
        if (
            self.result.csvpath.all_expected_files is None
            or len(self.result.csvpath.all_expected_files) == 0
        ):
            if not self.has_file("meta.json"):
                return False
            if not self.has_file("errors.json"):
                return False
            if not self.has_file("vars.json"):
                return False
            return True
        for t in self.result.csvpath.all_expected_files:
            t = t.strip()
            if t.startswith("no-data"):
                if self.has_file("data.csv"):
                    return False
            if t.startswith("data") or t.startswith("all"):
                if not self.has_file("data.csv"):
                    return False
            if t.startswith("no-unmatched"):
                if self.has_file("unmatched.csv"):
                    return False
            if t.startswith("unmatched") or t.startswith("all"):
                if not self.has_file("unmatched.csv"):
                    return False
            if t.startswith("no-printouts"):
                if self.has_file("printouts.txt"):
                    return False
            if t.startswith("printouts") or t.startswith("all"):
                if not self.has_file("printouts.txt"):
                    return False
            if not self.has_file("meta.json"):
                return False
            if not self.has_file("errors.json"):
                return False
            if not self.has_file("vars.json"):
                return False
        return True

    def has_file(self, t: str) -> bool:
        r = self.result_path
        return os.path.exists(os.path.join(r, t))

    @property
    def file_fingerprints(self) -> dict[str]:
        r = self.result_path
        fps = {}
        for t in [
            "data.csv",
            "meta.json",
            "unmatched.csv",
            "printouts.txt",
            "errors.json",
            "vars.json",
        ]:
            f = self._fingerprint(os.path.join(r, t))
            if f is None:
                continue
            fps[t] = f
        return fps

    def _fingerprint(self, path) -> str:
        if os.path.exists(path):
            with open(path, "rb") as f:
                h = hashlib.file_digest(f, hashlib.sha256)
                h = h.hexdigest()
            return h
        return None
