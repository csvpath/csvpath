import os
import json
import hashlib
import shutil
from datetime import datetime
from ..util.exceptions import InputException
from ..util.file_readers import DataFileReader


class FileRegistrar:
    def __init__(self, config):
        self.config = config

    @property
    def named_files_dir(self) -> str:
        return self.config.inputs_files_path

    def _simple_name(self, path) -> str:
        i = path.rfind(os.sep)
        sname = None
        if i == -1:
            sname = path
        else:
            sname = path[i + 1 :]
        return sname

    def named_file_home(self, name: str) -> str:
        home = os.path.join(self.named_files_dir, name)
        return home

    def assure_named_file_home(self, name: str) -> str:
        home = self.named_file_home(name)
        if not os.path.exists(home):
            os.makedirs(home)
        return home

    def assure_file_home(self, name: str, path: str) -> str:
        fname = self._simple_name(path)
        home = self.named_file_home(name)
        home = os.path.join(home, fname)
        if not os.path.exists(home):
            os.makedirs(home)
        return home

    def _copy_in(self, path, home) -> None:
        fname = self._simple_name(path)
        # creates
        #   a/file.csv -> named_files/name/file.csv/file.csv
        # the dir name matching the resulting file name is correct
        # once the file is landed and fingerprinted, the file
        # name is changed.
        temp = os.path.join(home, fname)
        if path.startswith("s3:"):
            self._copy_down(path, temp)
        else:
            shutil.copy(path, temp)
        return temp

    def _copy_down(self, path, temp) -> None:
        reader = DataFileReader(path)
        with open(temp, "w", encoding="utf-8") as file:
            for line in reader.next_raw():
                file.write(line)

    def _fingerprint(self, path) -> str:
        fname = self._simple_name(path)
        t = None
        i = fname.find(".")
        if i > -1:
            t = fname[i + 1 :]
        i = t.find("#")
        if i > -1:
            t = t[0:i]
        fpath = os.path.join(path, fname)
        with open(fpath, "rb") as f:
            h = hashlib.file_digest(f, hashlib.sha256)
            h = h.hexdigest()
        hpath = os.path.join(path, h)
        if t is not None:
            hpath = f"{hpath}.{t}"
        b = os.path.exists(hpath)
        if b:
            os.remove(fpath)
            return hpath, h
        os.rename(fpath, hpath)
        return hpath, h

    def manifest_path(self, name) -> str:
        nhome = self.named_file_home(name)
        mf = os.path.join(nhome, "manifest.json")
        if not os.path.exists(mf):
            self.assure_named_file_home(name)
            with open(mf, "w", encoding="utf-8") as file:
                file.write("[]")
        return mf

    def get_manifest(self, mpath) -> list:
        with open(mpath, "r", encoding="utf-8") as file:
            return json.load(file)

    def update_manifest(
        self,
        *,
        manifestpath: str,
        regpath: str,
        sourcepath: str,
        fingerprint: str,
        mark: str = None,
    ) -> None:
        t = self.type_from_sourcepath(sourcepath)
        mdata = {}
        mdata["type"] = t
        mdata["file"] = regpath
        mdata["fingerprint"] = fingerprint
        mdata["time"] = f"{datetime.now()}"
        mdata["from"] = sourcepath
        if mark is not None:
            mdata["mark"] = mark
        jdata = self.get_manifest(manifestpath)
        jdata.append(mdata)
        with open(manifestpath, "w", encoding="utf-8") as file:
            json.dump(jdata, file)

    def register_named_file(self, *, name: str, path: str) -> None:
        # does the source file exist?
        i = path.find("#")
        mark = None
        if i > -1:
            mark = path[i + 1 :]
            path = path[0:i]

        if not path.startswith("s3:") and not os.path.exists(path):
            #
            # try for a data reader in case we're smart-opening
            #
            raise InputException(f"Path {path} does not exist")
        #
        # create folder tree in inputs/named_files/name/filename
        #
        home = self.assure_file_home(name, path)
        #
        # copy file to its home location
        #
        self._copy_in(path, home)
        #
        # fingerprint file
        # does the fingerprint already exist?
        # rename file to fingerprint
        #
        rpath, h = self._fingerprint(home)
        #
        # create inputs/named_files/name/manifest.json
        # add line in manifest with date->fingerprint->source-location->reg-file-location
        # return path to current / most recent registered file
        #
        mpath = self.manifest_path(name)
        #
        # append the metadata
        #
        self.update_manifest(
            manifestpath=mpath, regpath=rpath, sourcepath=path, fingerprint=h, mark=mark
        )
        #
        # return the registered path
        #
        return rpath

    def type_of_file(self, name: str) -> str:
        p = self.manifest_path(name)
        m = self.get_manifest(p)
        return m[len(m) - 1]["type"]

    def type_from_sourcepath(self, sourcepath: str) -> str:
        i = sourcepath.rfind(".")
        t = "Unknown type"
        if i > -1:
            # raise InputException(f"Cannot guess file type without extension: {sourcepath}")
            t = sourcepath[i + 1 :]
        i = t.find("#")
        if i > -1:
            t = t[0:i]
        return t

    def name_exists(self, name: str) -> bool:
        p = self.named_file_home(name)
        return os.path.exists(p)

    def registered_file(self, name: str) -> str:
        if not self.name_exists(name):
            return None
        mpath = self.manifest_path(name)
        with open(mpath, "r", encoding="utf-8") as file:
            mdata = json.load(file)
            if mdata is None or len(mdata) == 0:
                raise InputException(f"Manifest for {name} at {mpath} is empty")
            m = mdata[len(mdata) - 1]
            path = m["file"]
            mark = None
            if "mark" in m:
                mark = m["mark"]
            if mark is not None:
                path = f"{path}#{mark}"
            return path
