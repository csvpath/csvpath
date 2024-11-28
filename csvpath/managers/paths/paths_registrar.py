import os
import json
import hashlib
from datetime import datetime
from csvpath.util.exceptions import InputException
from .paths_metadata import PathsMetadata
from ..listener import Listener
from ..metadata import Metadata
from ..registrar import Registrar


class PathsRegistrar(Listener, Registrar):
    def __init__(self, *, manager, config):
        self.config = config
        self.manager = manager

    @property
    def named_paths_dir(self) -> str:
        return self.config.inputs_csvpaths_path

    def _simple_name(self, path) -> str:
        i = path.rfind(os.sep)
        sname = None
        if i == -1:
            sname = path
        else:
            sname = path[i + 1 :]
        return sname

    def store_json_paths_file(self, name: str, jsonpath: str) -> None:
        home = self.assure_named_paths_home(name)
        j = ""
        with open(jsonpath, "r", encoding="utf-8") as file:
            j = file.read()
        with open(os.path.join(home, "definition.json"), "w", encoding="utf-8") as file:
            file.write(j)

    def _fingerprint(self, name) -> str:
        home = self.named_paths_home(name)
        fpath = os.path.join(home, "group.csvpaths")
        if os.path.exists(fpath):
            with open(fpath, "rb") as f:
                h = hashlib.file_digest(f, hashlib.sha256)
                return h.hexdigest()
        return None

    def get_manifest(self, mpath) -> list:
        with open(mpath, "r", encoding="utf-8") as file:
            return json.load(file)

    def register(self, *, mdata: Metadata) -> None:
        self.assure_manifest(mdata.named_paths_name)
        mdata.manifest_path = self.assure_manifest(mdata.named_paths_name)
        mdata.fingerprint = self._fingerprint(mdata.named_paths_name)
        self.distribute_update(mdata)

    def metadata_update(self, mdata: Metadata) -> None:
        jdata = self.get_manifest(mdata.manifest_path)
        if len(jdata) == 0 or jdata[len(jdata) - 1]["fingerprint"] != mdata.fingerprint:
            mdata = {}
            mdata["file"] = mdata.named_paths_name
            mdata["fingerprint"] = mdata.fingerprint
            mdata["time"] = f"{mdata.time}"
            mdata["count"] = mdata.count
            mdata["manifest_path"] = mdata.manifest_path
            jdata.append(mdata)
            with open(mdata.manifest_path, "w", encoding="utf-8") as file:
                json.dump(jdata, file, indent=2)

    def assure_manifest(self, name: str) -> None:
        nhome = self.named_paths_home(name)
        mf = os.path.join(nhome, "manifest.json")
        if not os.path.exists(mf):
            self.assure_named_paths_home(name)
            with open(mf, "w", encoding="utf-8") as file:
                file.write("[]")
        return mf
