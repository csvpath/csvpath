import os
import time
import json
import hashlib
from datetime import datetime
from abc import ABC, abstractmethod
from ..util.exceptions import FileException


class CsvPathsRegistrar(ABC):
    @abstractmethod
    def update_manifest(
        self, *, filepath: str, instancepath: str, fingerprint: str
    ) -> None:
        pass


class CsvPathsFilesystemRegistrar(CsvPathsRegistrar):
    def __init__(self, csvpaths):
        self.csvpaths = csvpaths
        self.archive = self.csvpaths.config.archive_path

    @property
    def manifest_path(self) -> str:
        return os.path.join(self.archive, "manifest.json")

    @property
    def manifest(self) -> list:
        if not os.path.exists(self.archive):
            os.makedirs(self.archive, exist_ok=True)
        if not os.path.exists(self.manifest_path):
            with open(self.manifest_path, "w", encoding="utf-8") as file:
                json.dump([], file, indent=2)
        with open(self.manifest_path, "r", encoding="utf-8") as file:
            return json.load(file)

    def _fingerprint_file(self, path) -> str:
        with open(path, "rb") as f:
            h = hashlib.file_digest(f, hashlib.sha256)
            h = h.hexdigest()
        return h

    def size(self, path) -> str:
        try:
            return os.stat(path).st_size
        except FileNotFoundError:
            return 0

    def last_change(self, path) -> str:
        try:
            last_mod = os.stat(path).st_mtime
            last_mod = time.ctime(last_mod)
            return last_mod
        except FileNotFoundError:
            return -1

    def update_manifest(
        self,
        *,
        csvpath,
        filepath: str,
        instancepath: str,
        fingerprint: str,
        identity: str,
    ) -> None:
        ffingerprint = self._fingerprint_file(filepath)
        size = self.size(filepath)
        last_change = self.last_change(filepath)
        mdata = {}
        mdata["file_path"] = filepath
        mdata["file_size"] = size
        mdata["file_last_change"] = last_change
        mdata["fingerprint_provided"] = fingerprint
        mdata["fingerprint_found"] = ffingerprint
        mdata["time"] = f"{datetime.now()}"
        mdata["target"] = instancepath
        mdata["identity"] = identity
        jdata = self.manifest
        jdata.append(mdata)
        with open(self.manifest_path, "w", encoding="utf-8") as file:
            json.dump(jdata, file, indent=2)
        houf = self.csvpaths.config.halt_on_unmatched_file_fingerprints()
        if fingerprint != ffingerprint and csvpath.source_mode != "preceding":
            self.csvpaths.logger.warning(
                "fingerprints of input file %s do not agree: orig:%s != current:%s",
                filepath,
                fingerprint,
                ffingerprint,
            )
        if (
            houf is True
            and fingerprint != ffingerprint
            and csvpath.source_mode != "preceding"
        ):
            raise FileException(
                "File was modified since being registered. See manifest for %s at %s. Processing halted.",
                filepath,
                mdata["time"],
            )
