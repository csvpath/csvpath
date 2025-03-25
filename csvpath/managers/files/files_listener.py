import os
import json
from datetime import datetime
from csvpath.util.exceptions import InputException, FileException
from csvpath.util.file_readers import DataFileReader
from csvpath.util.file_writers import DataFileWriter
from csvpath.util.nos import Nos
from csvpath.managers.listener import Listener
from csvpath.managers.metadata import Metadata

#
# TODO: not using intermediary
#


class FilesListener(Listener):  # Registrar,
    """@private
    this listener tracks all named-file arrivals"""

    def __init__(self, csvpaths=None):
        #
        # FileListener is the primary listener. however,
        # we want another file listener that tracks all files
        # staged at the inputs/named_files level.
        #
        Listener.__init__(self, csvpaths.config if csvpaths else None)
        self.csvpaths = csvpaths
        self.config = None
        if self.csvpaths:
            self.config = csvpaths.config
        self.type_name = "files"

    def manifest_path(self) -> str:
        root = self.config.get(section="inputs", name="files")
        mf = os.path.join(root, "manifest.json")
        if not Nos(mf).exists():
            with DataFileWriter(path=mf, mode="w") as writer:
                writer.append("[]")
        return mf

    def get_manifest(self, mpath) -> list:
        with DataFileReader(mpath) as reader:
            return json.load(reader.source)

    def _core_from_metadata(self, mdata: Metadata) -> dict:
        mani = {}
        mani["time"] = mdata.time_string
        mani["uuid"] = mdata.uuid_string
        mani["file_manifest"] = mdata.manifest_path
        if mdata.username:
            mani["username"] = mdata.username
        if mdata.hostname:
            mani["hostname"] = mdata.hostname
        if mdata.ip_address:
            mani["ip_address"] = mdata.ip_address
        return mani

    def _prep_update(self, mdata: Metadata) -> dict:
        mani = self._core_from_metadata(mdata)
        mani["type"] = mdata.type
        mani["time"] = mdata.time_string
        mani["named_file_name"] = mdata.named_file_name
        mani["origin_path"] = mdata.origin_path
        mani["fingerprint"] = mdata.fingerprint
        mani["file_path"] = mdata.file_path
        mani["file_home"] = mdata.file_home
        mani["file_name"] = mdata.file_name
        mani["name_home"] = mdata.name_home
        if mdata.template is not None:
            mani["template"] = mdata.template
        if mdata.mark is not None:
            mani["mark"] = mdata.mark
        mani["manifest_path"] = self.manifest_path()
        return mani

    def metadata_update(self, mdata: Metadata) -> None:
        mani = self._prep_update(mdata)
        manifest_path = self.manifest_path()
        #
        # this will not be Ok for major implementations. there is a
        # potential for lost updates. however, for small or low risk
        # implementations it will work. replacing with a concurrancy-safe
        # listener would be straightforward. a future todo or some kind
        # of upgrade above the stock library?
        #
        jdata = self.get_manifest(manifest_path)
        jdata.append(mani)
        with DataFileWriter(path=manifest_path, mode="w") as writer:
            json.dump(jdata, writer.sink, indent=2)
