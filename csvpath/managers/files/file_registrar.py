import os
import json
from datetime import datetime
from csvpath.util.exceptions import InputException, FileException
from csvpath.util.nos import Nos
from csvpath.managers.registrar import Registrar
from csvpath.managers.listener import Listener
from csvpath.managers.metadata import Metadata
from csvpath.util.intermediary import Intermediary


class FileRegistrar(Registrar, Listener):
    """@private
    this file registers the metadata with a tracking system. e.g. an OpenLineage
    server, JSON file, or database"""

    def __init__(self, csvpaths):
        Registrar.__init__(self, csvpaths)
        Listener.__init__(self, csvpaths.config)
        self.csvpaths = csvpaths
        self.config = csvpaths.config
        self.type_name = "file"
        self.intermediary = Intermediary(csvpaths)

    def get_fingerprint(self, home) -> str:
        mpath = self.manifest_path(home)
        man = self.get_manifest(mpath)
        if man is None or len(man) == 0:
            raise FileException(
                f"No fingerprint available for named-file name: {home} at manifest path: {mpath}: manifest: {man}"
            )
        return man[len(man) - 1]["fingerprint"]

    def manifest_path(self, home) -> str:
        if home is None or home.strip() == "":
            raise ValueError("Home cannot be None or empty")
        nos = Nos(home)
        if nos.physical_dirs() and not nos.dir_exists():
            raise InputException(f"Named file home does not exist: {home}")
        mf = os.path.join(home, "manifest.json")
        nos.path = mf
        if not nos.exists():
            self.intermediary.put_json(mf, [])
        return mf

    def get_manifest(self, mpath) -> list:
        j = self.intermediary.get_json(mpath)
        if j is None:
            j = []
            self.intermediary.put_json(mpath, j)
        return j

    def patch_named_file(self, *, name, patch, index=-1) -> None:
        #
        # TODO: distribute an metadata event to give metadata stores a
        # chance to update their info re: the file
        #
        home = self.csvpaths.file_manager.named_file_home(name)
        mp = self.manifest_path(home)
        mani = self.get_manifest(mp)
        index = len(mani) - 1 if index == -1 else index
        if "type" in patch:
            #
            # obviously without a change in file_name the type is set in metadata only.
            #
            mani[index]["type"] = patch["type"]
        if "file_name" in patch:
            #
            # blob stores handle directories differently from filesystems.
            #
            if mani[index]["file"].find("://") > -1:
                self._patch_blob(mani, index, patch)
            else:
                self._patch_filesystem(mani, home=home, index=index, patch=patch)
        self.intermediary.put_json(mp, mani)

    def _patch_blob(self, mani: dict, index: int, patch: dict) -> None:
        old = mani[index]["file"]
        newhome = f"{os.path.dirname(mani[index]['file_home'])}/{patch['file_name']}"
        nos = Nos(newhome)
        if not nos.dir_exists():
            nos.makedir()
        new = f"{newhome}/{mani[index]['fingerprint']}.{mani[index]['type']}"
        nos = Nos(old)
        if not nos.exists():
            raise ValueError("File not found: {old}")
        nos.rename(new)
        mani[index]["file"] = new
        mani[index]["file_home"] = newhome

    def _patch_filesystem(
        self, mani: dict, *, home: str, index: int, patch: dict
    ) -> None:
        sep = os.sep
        #
        # we can assume that if we're setting the file name the type may have changed
        # and could be a problem. so we rename to fingerprint + type based on current info.
        # then we rename the file home to the new file name we've been given.
        #
        # 1. move file to fingerprint.type
        # 2. move file home to home/new_file_name
        #
        old_file = mani[index]["file"]
        new_file = f"{mani[index]['file_home']}{sep}{mani[index]['fingerprint']}.{mani[index]['type']}"
        nos = Nos(None)
        nos.path = old_file
        nos.rename(new_file)
        old_home = mani[index]["file_home"]
        new_home = f"{home}{sep}{patch['file_name']}"
        nos.path = old_home
        nos.rename(new_home)
        mani[index]["file_home"] = new_home
        mani[index][
            "file"
        ] = f"{new_home}{sep}{mani[index]['fingerprint']}.{mani[index]['type']}"

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
        mani["uuid"] = mdata.uuid_string
        mani["time"] = mdata.time_string
        mani["from"] = path
        if mark is not None:
            mani["mark"] = mark
        if mdata.template is not None:
            mani["template"] = mdata.template
        jdata = self.get_manifest(manifest_path)
        jdata.append(mani)
        self.intermediary.put_json(manifest_path, jdata)
        #
        # drop update into an all-inputs/files record here?
        #

    def register_complete(self, mdata: Metadata) -> None:
        path = mdata.origin_path
        home = mdata.name_home
        if path is None or path.strip() == "":
            raise ValueError("Path cannot be None or empty")
        if home is None or home.strip() == "":
            raise ValueError("Home cannot be None or empty")
        i = path.find("#")
        mark = None
        if i > -1:
            mark = path[i + 1 :]
            path = path[0:i]
        if mark != mdata.mark:
            raise InputException(
                f"File mgr and registrar marks should match: {mdata.mark}, {mark}"
            )
        if (
            # Nos doesn't handle http files. they are special--inbound only.
            not path.startswith("http:")
            and not path.startswith("https:")
            and not Nos(path).exists()
        ):
            # if not path.startswith("s3:") and not os.path.exists(path):
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
        for _ in jdata:
            #
            # if the fingerprints are the same and we haven't renamed
            # the file or moved all the files we don't need to reregister
            # this file. at least that is the thinking today. it is possible
            # we might want to reregister in the case of a new listener
            # being added or for some other reason, but not atm.
            #
            if (
                "fingerprint" in _
                and _["fingerprint"] == mdata.fingerprint
                and "file_home" in _
                and _["file_home"].lower() == mdata.file_home.lower()
            ):
                #
                # log info so nobody has to dig to see why no update
                #
                self.csvpaths.logger.info(
                    "File has already been registered: %s", mdata.name_home
                )
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
        mdata = self.get_manifest(mpath)
        if mdata is None or len(mdata) == 0:
            raise InputException(f"Manifest for {home} at {mpath} is empty")
        m = mdata[len(mdata) - 1]
        if "file" not in m:
            raise ValueError(
                "File path cannot be None. Check your config file and named-files."
            )
        path = m["file"]
        mark = None
        if "mark" in m:
            mark = m["mark"]
        if mark is not None:
            path = f"{path}#{mark}"
        return path
