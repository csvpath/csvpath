import os
import json
import hashlib
from csvpath.util.exceptions import InputException
from .paths_metadata import PathsMetadata
from ..listener import Listener
from ..metadata import Metadata
from ..registrar import Registrar


class PathsRegistrar(Registrar, Listener):
    def __init__(self, csvpaths):
        super().__init__(csvpaths)
        self._manager = None
        self.load_additional_listeners("paths")

    @property
    def manager(self):
        if self._manager is None:
            self._manager = self.csvpaths.paths_manager
        return self._manager

    def get_manifest(self, mpath) -> list:
        with open(mpath, "r", encoding="utf-8") as file:
            return json.load(file)

    def register_complete(self, mdata: Metadata) -> None:
        mdata.manifest_path = self.manifest_path(name=mdata.named_paths_name)
        mdata.fingerprint = self._fingerprint(name=mdata.named_paths_name)
        self.distribute_update(mdata)

    def update_manifest_if(self, *, group_file_path, name, paths=None):
        #
        # if we find that the current group file does not have the same
        # fingerprint as the most recent on file, we register a new version.
        # this is not the expected way things work, but if someone makes an
        # update in place, without re-adding the named-paths, this is what
        # happens.
        #
        f = self._fingerprint(group_file_path=group_file_path)
        mpath = self.manifest_path(name)
        cf = self._most_recent_fingerprint(mpath)
        if f != cf:
            mdata = PathsMetadata()
            mdata.archive_name = self.csvpaths.config.archive_name
            mdata.named_paths_name = name
            mdata.named_paths_file = group_file_path
            mdata.named_paths = paths
            mdata.group_file_path = group_file_path
            mdata.named_paths_identities = [
                t[0] for t in self.manager.get_identified_paths_in(name)
            ]
            if paths:
                mdata.named_paths_count = len(paths)
            mdata.manifest_path = mpath
            mdata.fingerprint = f
            self.distribute_update(mdata)

    def metadata_update(self, mdata: Metadata) -> None:
        jdata = self.get_manifest(mdata.manifest_path)
        if len(jdata) == 0 or jdata[len(jdata) - 1]["fingerprint"] != mdata.fingerprint:
            m = {}
            #
            # the inputs dir may be outside the archive dir, as by default, or
            # inside. regardless, the point is that archive is the namespace.
            # the inputs dirs are intended to stage assets for the archive
            # regardless of if they are located in the archive or not.
            #
            m["archive_name"] = mdata.archive_name
            m["named_paths_name"] = mdata.named_paths_name
            m["named_paths_home"] = mdata.named_paths_home
            m["group_file_path"] = mdata.group_file_path
            m["named_paths"] = mdata.named_paths
            m["named_paths_identities"] = mdata.named_paths_identities
            m["named_paths_count"] = mdata.named_paths_count
            m["fingerprint"] = mdata.fingerprint
            m["time"] = mdata.time_string
            if mdata.time_started is not None:
                m["time_started"] = mdata.time_started_string
            if mdata.time_completed is not None:
                m["time_completed"] = mdata.time_completed_string
            m["uuid"] = mdata.uuid_string
            m["manifest_path"] = mdata.manifest_path
            jdata.append(m)
            with open(mdata.manifest_path, "w", encoding="utf-8") as file:
                json.dump(jdata, file, indent=2)

    def manifest_path(self, name: str) -> None:
        nhome = self.manager.named_paths_home(name)
        mf = os.path.join(nhome, "manifest.json")
        if not os.path.exists(mf):
            with open(mf, "w", encoding="utf-8") as file:
                file.write("[]")
        return mf

    def _most_recent_fingerprint(self, manifest_path: str) -> str:
        jdata = self.get_manifest(manifest_path)
        if len(jdata) == 0:
            return None
        return jdata[len(jdata) - 1]["fingerprint"]

    def _simple_name(self, path) -> str:
        i = path.rfind(os.sep)
        sname = None
        if i == -1:
            sname = path
        else:
            sname = path[i + 1 :]
        return sname

    def _fingerprint(self, *, name=None, group_file_path=None) -> str:
        if group_file_path is None and name is not None:
            home = self.manager.named_paths_home(name)
            group_file_path = os.path.join(home, "group.csvpaths")
        elif group_file_path is None and name is None:
            raise InputException(
                "Either the named-paths name or the path to the group file must be provided"
            )
        if os.path.exists(group_file_path):
            with open(group_file_path, "rb") as f:
                h = hashlib.file_digest(f, hashlib.sha256)
                return h.hexdigest()
        return None
