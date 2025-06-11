import os
import time
import json
from abc import ABC, abstractmethod
from csvpath.util.exceptions import FileException
from csvpath.util.file_writers import DataFileWriter
from csvpath.util.file_readers import DataFileReader
from csvpath.util.nos import Nos
from ..listener import Listener
from ..registrar import Registrar
from ..metadata import Metadata


class RunRegistrar(Registrar, Listener):
    def __init__(self, csvpaths):
        # super().__init__(csvpaths)
        Registrar.__init__(self, csvpaths)
        Listener.__init__(self, csvpaths.config)
        self.type_name = "run"
        self.archive = self.csvpaths.config.archive_path

    @property
    def manifest_path(self) -> str:
        return os.path.join(self.archive, "manifest.json")

    @property
    def manifest(self) -> list:
        if not Nos(self.archive).exists():
            Nos(self.archive).makedirs()
        if not Nos(self.manifest_path).exists():
            with DataFileWriter(path=self.manifest_path) as file:
                json.dump([], file.sink, indent=2)
        with DataFileReader(self.manifest_path) as file:
            return json.load(file.source)

    def metadata_update(self, mdata: Metadata) -> None:
        m = {}
        m["time"] = f"{mdata.time}"
        m["run_uuid"] = mdata.run_uuid_string
        m["run_home"] = mdata.run_home
        m["identity"] = mdata.identity
        m["named_paths_name"] = mdata.named_paths_name
        m["named_file_name"] = mdata.named_file_name
        mp = self.manifest_path
        m["manifest_path"] = mp
        #
        # adding to help make clearer where assets are for each
        # run. we now have the potential for much more flexibility.
        # it is possible that this is not enough identification.
        #
        m["archive_name"] = mdata.archive_name
        m["archive_path"] = mdata.archive_path
        m["base_path"] = mdata.base_path
        m["named_files_root"] = mdata.named_files_root
        m["named_paths_root"] = mdata.named_paths_root
        #
        #
        #
        mani = self.manifest
        mani.append(m)
        with DataFileWriter(path=mp) as file:
            json.dump(mani, file.sink, indent=2)
