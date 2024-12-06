import os
import json
import hashlib
import shutil
from datetime import datetime
from csvpath.util.exceptions import InputException, FileException
from csvpath.util.file_readers import DataFileReader
from csvpath.managers.registrar import Registrar
from csvpath.managers.listener import Listener
from csvpath.managers.metadata import Metadata


class FileRegistrar(Registrar, Listener):
    """this file registers the metadata with a tracking system. e.g. an OpenLineage
    server, JSON file, or database"""

    def __init__(self, csvpaths):
        super().__init__(csvpaths)
        self.csvpaths = csvpaths
        self.config = csvpaths.config
        self.load_additional_listeners("file")

    def get_fingerprint(self, home) -> str:
        mpath = self.manifest_path(home)
        man = self.get_manifest(mpath)
        if man is None or len(man) == 0:
            raise FileException(
                f"No fingerprint available for named-file name: {home} at manifest path: {mpath}: manifest: {man}"
            )
        return man[len(man) - 1]["fingerprint"]

    def manifest_path(self, home) -> str:
        if not os.path.exists(home):
            raise InputException(f"Named file home does not exist: {home}")
        mf = os.path.join(home, "manifest.json")
        if not os.path.exists(mf):
            with open(mf, "w", encoding="utf-8") as file:
                file.write("[]")
        return mf

    def get_manifest(self, mpath) -> list:
        with open(mpath, "r", encoding="utf-8") as file:
            return json.load(file)

    def metadata_update(self, mdata: Metadata) -> None:
        path = mdata.origin_path
        rpath = mdata.file_path
        h = mdata.fingerprint
        t = mdata.type
        mark = mdata.mark
        manifest_path = mdata.manifest_path
        mani = {}
        mani["type"] = t
        mani["file"] = rpath
        mani["file_home"] = mdata.file_home
        mani["fingerprint"] = h
        mani["time"] = mdata.time_string
        mani["from"] = path
        if mark is not None:
            mani["mark"] = mark
        jdata = self.get_manifest(manifest_path)
        jdata.append(mani)
        with open(manifest_path, "w", encoding="utf-8") as file:
            json.dump(jdata, file, indent=2)

    def register_complete(self, mdata: Metadata) -> None:
        path = mdata.origin_path
        home = mdata.name_home
        i = path.find("#")
        mark = None
        if i > -1:
            mark = path[i + 1 :]
            path = path[0:i]
        if mark != mdata.mark:
            raise InputException(
                f"File mgr and registrar marks should match: {mdata.mark}, {mark}"
            )
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
        # create inputs/named_files/name/manifest.json
        # add line in manifest with date->fingerprint->source-location->reg-file-location
        # return path to current / most recent registered file
        #
        mpath = self.manifest_path(home=home)
        mdata.manifest_path = mpath
        mdata.type = self._type_from_sourcepath(path)
        jdata = self.get_manifest(mpath)
        if len(jdata) > 0:
            _ = jdata[len(jdata) - 1]
            # if the fingerprints are the same and we haven't renamed
            # the file or moved all the files we don't need to reregister
            # this file. at least that is the thinking today. it is possible
            # we might want to reregister in the case of a new listener
            # being added or for some other reason, but not atm.
            if (
                "fingerprint" in _
                and _["fingerprint"] == mdata.fingerprint
                and "file_home" in _
                and _["file_home"] == mdata.file_home
            ):
                self.csvpaths.logger.info("File has already been registered: %s", jdata)
                return
        self.distribute_update(mdata)

    def type_of_file(self, home: str) -> str:
        p = self.manifest_path(home)
        m = self.get_manifest(p)
        return m[len(m) - 1]["type"]

    def _type_from_sourcepath(self, sourcepath: str) -> str:
        i = sourcepath.rfind(".")
        t = "Unknown type"
        if i > -1:
            t = sourcepath[i + 1 :]
        i = t.find("#")
        if i > -1:
            t = t[0:i]
        return t

    def registered_file(self, home: str) -> str:
        mpath = self.manifest_path(home)
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
