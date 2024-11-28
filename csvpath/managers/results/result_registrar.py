import os
import json
import hashlib
from datetime import datetime
from ..listener import Listener
from ..metadata import Metadata
from ..registrar import Registrar
from .result_metadata import ResultMetadata


class ResultRegistrar(Registrar, Listener):
    def __init__(self, *, result, result_serializer):
        self.result = result
        self.result_serializer = result_serializer

    def register(self, mdata: Metadata = None) -> None:
        #
        # results manager delegates the bits to the
        # serializer and the metadata assembly to this
        # registrar, so we expect it to hand us nothing
        # but the result object and serializer.
        #
        if mdata is None:
            mdata = ResultMetadata()
            mdata.archive_name = self._archive_name
            mdata.named_results_name = self.result.paths_name
            mdata.instance = self.result.run_time
            mdata.instance_dir = self.result.instance_dir
            mdata.identity = self.result.identity_or_index
            mdata.input_data_file = self.result.file_name
            mdata.file_fingerprints = self.file_fingerprints
            mdata.file_count = len(mdata.file_fingerprints)
            mdata.valid = self.result.csvpath.is_valid
            mdata.completed = self.completed
            mdata.expected = self.all_expected_files
            mdata.transfers = self.result.csvpath.transfers
        self.distribute_update(mdata)

    def metadata_update(self, mdata: Metadata) -> None:
        m = {}
        m["archive_name"] = mdata.archive_name
        m["named_results_name"] = mdata.named_results_name
        m["instance"] = mdata.instance
        m["instance_dir"] = mdata.instance_dir
        m["identity"] = mdata.identity
        m["file_fingerprints"] = mdata.file_fingerprints
        m["files_expected"] = mdata.expected
        m["file_count"] = mdata.file_count
        m["valid"] = mdata.valid
        m["time"] = f"{mdata.time}"
        m["completed"] = mdata.completed
        m["input_data_file"] = mdata.input_data_file
        m["transfers"] = mdata.transfers
        mp = self.manifest_path
        m["manifest_path"] = mp
        with open(mp, "w", encoding="utf-8") as file:
            json.dump(m, file, indent=2)

    def _archive_name(self) -> str:
        ap = self.result.csvpath.config.archive_path
        i = ap.rfind(os.sep)
        if i > 0:
            return ap[i + 1 :]
        return ap

    @property
    def manifest(self) -> dict[str, str | bool]:
        with open(self.manifest_path, "r", encoding="utf-8") as file:
            d = json.load(file)
            return d
        return None

    @property
    def manifest_path(self) -> str:
        return os.path.join(self.result_path, "manifest.json")

    @property
    def result_path(self) -> str:
        rdir = self.result_serializer.get_instance_dir(
            run_dir=self.result.run_dir, identity=self.result.identity_or_index
        )
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
