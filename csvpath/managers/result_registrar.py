import os
import json
import hashlib
from datetime import datetime


class ResultRegistrar:
    def __init__(self, *, result, result_serializer):
        self.result = result
        self.result_serializer = result_serializer

    def write_manifest(self) -> None:
        m = {}
        #  - file fingerprints
        #  - validity
        #  - timestamp
        #  - run-completeness
        #  - files-expectedness
        ffs = self.file_fingerprints
        valid = self.result.csvpath.is_valid
        time = f"{datetime.now()}"
        completed = self.completed
        expected = self.all_expected_files
        m["file_fingerprints"] = ffs
        m["valid"] = valid
        m["time"] = time
        m["completed"] = completed
        m["files_expected"] = expected
        mp = self.manifest_path
        with open(mp, "w", encoding="utf-8") as file:
            json.dump(m, file, indent=2)

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
