import os
import json
import hashlib
import shutil
from datetime import datetime
from csvpath.util.exceptions import InputException, FileException
from csvpath.util.file_readers import DataFileReader


class FileRegistrar:
    """this file registers the metadata with a tracking system. e.g. an OpenLinage
    server, JSON file, or database"""

    def __init__(self, config):
        self.config = config

    def get_fingerprint(self, home) -> str:
        mpath = self.manifest_path(home)
        man = self.get_manifest(mpath)
        if man is None or len(man) == 0:
            raise FileException(
                f"No fingerprint available for named-file name: {home} at manifest path: {mpath}: manifest: {man}"
            )
        return man[len(man) - 1]["fingerprint"]

    def manifest_path(self, home) -> str:
        print(f"mp 1: home: {home}")
        if not os.path.exists(home):
            raise InputException(f"Named file home does not exist: {home}")
        mf = os.path.join(home, "manifest.json")
        print(f"mp 2: mf: {mf}")
        if not os.path.exists(mf):
            with open(mf, "w", encoding="utf-8") as file:
                file.write("[]")
        print(f"mp 3: returning: {mf}")
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
            json.dump(jdata, file, indent=2)

    def register_named_file(
        self,
        *,
        name: str,
        path: str,
        home: str,
        file_home: str,
        rpath: str,
        h: str,
    ) -> str:
        #
        # rpath is the fingerprinted file path
        # h is the hash fingerprint itself
        #
        #
        # check does the source file exist?
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
        # if the fingerprint already exists we don't store the file again.
        # we rename the file to the fingerprint. from this point the registrar
        # is responsible for the location of the current version of the file.
        # that is approprate because the file manager isn't responsible for
        # identification, only divvying up activity between its workers,
        # the initial file drop off to them, and responding to external
        # requests.
        #
        print(
            f"rnf 1: name: {name}, path: {path}, home: {home}, file_home: {file_home}"
        )
        # rpath, h = self._fingerprint(file_home)
        #
        # create inputs/named_files/name/manifest.json
        # add line in manifest with date->fingerprint->source-location->reg-file-location
        # return path to current / most recent registered file
        #
        mpath = self.manifest_path(home=home)
        print(f"rnf 2: home: {home}, mpath: {mpath}, name: {name}")
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

    def type_of_file(self, home: str) -> str:
        p = self.manifest_path(home)
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

    def registered_file(self, home: str) -> str:
        print(f"frrf 1: home: {home}")
        mpath = self.manifest_path(home)
        print(f"frrf 2: mpath: {mpath}")
        with open(mpath, "r", encoding="utf-8") as file:
            mdata = json.load(file)
            if mdata is None or len(mdata) == 0:
                raise InputException(f"Manifest for {home} at {mpath} is empty")
            m = mdata[len(mdata) - 1]
            path = m["file"]
            mark = None
            if "mark" in m:
                mark = m["mark"]
            if mark is not None:
                path = f"{path}#{mark}"
            return path
