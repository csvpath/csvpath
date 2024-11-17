import os
import json
import hashlib
from datetime import datetime
from ..util.exceptions import InputException


class PathsRegistrar:
    def __init__(self, config):
        self.config = config

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

    def named_paths_home(self, name: str) -> str:
        home = os.path.join(self.named_paths_dir, name)
        return home

    def assure_named_paths_home(self, name: str) -> str:
        home = self.named_paths_home(name)
        if not os.path.exists(home):
            os.makedirs(home)
        return home

    def _copy_in(self, name, csvpathstr) -> None:
        temp = self._group_file_path(name)
        with open(temp, "w", encoding="utf-8") as file:
            file.write(csvpathstr)
        return temp

    def _group_file_path(self, name: str) -> str:
        temp = os.path.join(self.named_paths_home(name), "group.csvpaths")
        return temp

    def str_from_list(self, paths: list[str]) -> str:
        f = ""
        for _ in paths:
            f = f"{f}\n\n---- CSVPATH ----\n\n{_}"
        return f

    def store_json_paths_file(self, name: str, jsonpath: str) -> None:
        home = self.assure_named_paths_home(name)
        j = ""
        with open(jsonpath, "r", encoding="utf-8") as file:
            j = file.read()
        with open(os.path.join(home, "definition.json"), "w", encoding="utf-8") as file:
            file.write(j)

    def _remove_group_file(self, name: str) -> None:
        t = self._group_file_path(name)
        if os.path.exists(t):
            os.remove(t)

    def register_named_paths(self, *, name: str, paths: list[str]) -> None:
        self.assure_named_paths_home(name)
        # when we pass a list it is complete and over-writes. we shouldn't
        # necesarily need to delete the group file, but being explicit
        # doesn't hurt.
        self._remove_group_file(name)
        s = self.str_from_list(paths)
        t = self._copy_in(name, s)
        mpath = self.assure_manifest(name)
        self.update_manifest(name=name, manifestpath=mpath, pathspath=t)
        return t

    def _fingerprint(self, name) -> str:
        home = self.named_paths_home(name)
        fpath = os.path.join(home, "group.csvpaths")
        with open(fpath, "rb") as f:
            h = hashlib.file_digest(f, hashlib.sha256)
            return h.hexdigest()

    def get_manifest(self, mpath) -> list:
        with open(mpath, "r", encoding="utf-8") as file:
            return json.load(file)

    def update_manifest_if(self, *, name, pathspath: str = "Unknown") -> None:
        self.update_manifest(
            name=name, manifestpath=self.assure_manifest(name), pathspath=pathspath
        )

    def update_manifest(self, *, name, manifestpath: str, pathspath: str) -> None:
        jdata = self.get_manifest(manifestpath)
        f = self._fingerprint(name)
        if len(jdata) == 0 or jdata[len(jdata) - 1]["fingerprint"] != f:
            mdata = {}
            mdata["file"] = pathspath
            mdata["fingerprint"] = f
            mdata["time"] = f"{datetime.now()}"
            jdata.append(mdata)
            with open(manifestpath, "w", encoding="utf-8") as file:
                json.dump(jdata, file)

    def assure_manifest(self, name: str) -> None:
        nhome = self.named_paths_home(name)
        mf = os.path.join(nhome, "manifest.json")
        if not os.path.exists(mf):
            self.assure_named_paths_home(name)
            with open(mf, "w", encoding="utf-8") as file:
                file.write("[]")
        return mf

    def name_exists(self, name: str) -> bool:
        p = self.named_paths_home(name)
        return os.path.exists(p)
