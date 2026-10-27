import json
from csvpath.util.file_readers import DataFileReader
from csvpath.util.file_writers import DataFileWriter
from csvpath.util.nos import Nos
from csvpath.util.ledger_utility import LedgerUtility as leut
from ..listener import Listener
from ..metadata import Metadata
from ..registrar import Registrar


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
    def __init__(self, *, config=None, csvpaths=None):
        Listener.__init__(self, csvpaths.config if csvpaths else config)
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
            # print(f"pathslist: mpath: {mpath}: {contents}")
            j = json.loads(contents)
            return j

    @property
    def manifest_path(self) -> None:
        mf = Nos(self.csvpaths.config.inputs_csvpaths_path).join("manifest.json")
        if not Nos(mf).exists():
            with DataFileWriter(path=mf) as file:
                file.append("[]")
        return mf

    def _prep_update(self, mdata: Metadata) -> dict:
        #
        # every ledger entry has a status; none is implied by absence
        #
        if mdata.status is None:
            raise ValueError("A named-paths ledger entry requires a status")
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
        mani["status"] = mdata.status
        mani["lifecycle"] = Registrar.ACTIVE
        if getattr(mdata, "version_uuid", None) is not None:
            mani["version_uuid"] = mdata.version_uuid
        mani["paths_manifest"] = mdata.manifest_path
        mani["manifest_path"] = self.manifest_path
        return mani

    def metadata_update(self, mdata: Metadata) -> None:
        mani = self._prep_update(mdata)
        jdata = self.manifest
        jdata.append(mani)
        with DataFileWriter(path=self.manifest_path) as file:
            j = json.dumps(jdata, indent=2)
            file.sink.write(j)
            file.sink.flush()
        mdata.ledger_entry = mani
        mdata.ledger_index = len(jdata) - 1

    def metadata_delete(self, mdata: Metadata) -> None:
        """marks every ledger entry for the deleted name, including
        unchanged reloads, in place. the ledger keeps them: it is the
        history."""
        if mdata is None:
            raise ValueError("Metadata cannot be None")
        if mdata.change is None:
            raise ValueError("Metadata has no delete change")
        jdata = self.manifest
        marked = leut.mark_deleted(
            jdata=jdata,
            name_key="named_paths_name",
            name=mdata.named_paths_name,
            change=mdata.change,
            deleted=Registrar.DELETED,
        )
        if len(marked) > 0:
            with DataFileWriter(path=self.manifest_path) as file:
                j = json.dumps(jdata, indent=2)
                file.sink.write(j)
                file.sink.flush()
        mdata.ledger_entries = marked
