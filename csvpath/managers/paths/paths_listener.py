import os
import json
from csvpath.util.exceptions import InputException
from csvpath.util.file_readers import DataFileReader
from csvpath.util.file_writers import DataFileWriter
from csvpath.util.nos import Nos
from .paths_metadata import PathsMetadata
from ..listener import Listener
from ..metadata import Metadata


class PathsListener(Listener):
    """@private"""

    #
    # PathsRegistrar is the primary listener. this listener
    # tracks all named-paths groups loaded to inputs/named_paths
    # in a manifest.json. Like FilesListener it has the potential
    # for lost updates if used in a situation where there could
    # be concurrent writes. if that is the situation it can be
    # turned off and/or replaced with a database-backed version.
    #
    def __init__(self, csvpaths=None):
        Listener.__init__(self, csvpaths.config if csvpaths else None)
        self.csvpaths = csvpaths
        self._manager = None
        self.type_name = "paths"

    @property
    def manager(self):
        if self._manager is None:
            self._manager = self.csvpaths.paths_manager
        return self._manager

    @property
    def manifest(self) -> list:
        mpath = self.manifest_path
        with DataFileReader(mpath, encoding="utf-8") as file:
            contents = file.read()
            j = json.loads(contents)
            # j = json.load(file.source)
            return j

    @property
    def manifest_path(self) -> None:
        mf = os.path.join(self.csvpaths.config.inputs_csvpaths_path, "manifest.json")
        if not Nos(mf).exists():
            with DataFileWriter(path=mf) as file:
                file.append("[]")
        return mf

    def _prep_update(self, mdata: Metadata) -> dict:
        mani = {}
        mani["named_paths_name"] = mdata.named_paths_name
        mani["named_paths_home"] = mdata.named_paths_home
        mani["group_file_path"] = mdata.group_file_path
        mani["source_path"] = mdata.source_path
        mani["fingerprint"] = mdata.fingerprint
        mani["time"] = mdata.time_string
        mani["uuid"] = mdata.uuid_string
        if mdata.username:
            mani["username"] = mdata.username
        if mdata.hostname:
            mani["hostname"] = mdata.hostname
        if mdata.ip_address:
            mani["ip_address"] = mdata.ip_address
        mani["paths_manifest"] = mdata.manifest_path
        mani["manifest_path"] = self.manifest_path
        return mani

    def metadata_update(self, mdata: Metadata) -> None:
        mani = self._prep_update(mdata)
        jdata = self.manifest
        jdata.append(mani)
        with DataFileWriter(path=self.manifest_path) as file:
            json.dump(jdata, file.sink, indent=2)
