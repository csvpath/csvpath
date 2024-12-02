import os
import time
import json
import hashlib
from abc import ABC, abstractmethod
from csvpath.util.exceptions import FileException
from ..listener import Listener
from ..registrar import Registrar
from ..metadata import Metadata


class RunRegistrar(Registrar, Listener):
    def __init__(self, csvpaths):
        super().__init__(csvpaths)
        #
        # add additional listeners here if any. e.g.
        #   self.add_listener(StdOutRunListener())
        # we're going to get them from [listeners] in config.ini. e.g.
        #    [listeners]
        #    run=from csvpath.managers.run.std_out_listener import StdOutListener
        #
        self.load_additional_listeners("run")
        self.archive = self.csvpaths.config.archive_path

    @property
    def manifest_path(self) -> str:
        return os.path.join(self.archive, "manifest.json")

    @property
    def manifest(self) -> list:
        if not os.path.exists(self.archive):
            os.makedirs(self.archive, exist_ok=True)
        if not os.path.exists(self.manifest_path):
            with open(self.manifest_path, "w", encoding="utf-8") as file:
                json.dump([], file, indent=2)
        with open(self.manifest_path, "r", encoding="utf-8") as file:
            return json.load(file)

    def metadata_update(self, mdata: Metadata) -> None:
        m = {}
        m["time"] = f"{mdata.time}"
        m["run_home"] = mdata.run_home
        m["identity"] = mdata.identity
        m["named_paths_name"] = mdata.named_paths_name
        m["named_file_name"] = mdata.named_file_name
        mp = self.manifest_path
        m["manifest_path"] = mp
        mani = self.manifest
        mani.append(m)
        with open(mp, "w", encoding="utf-8") as file:
            json.dump(mani, file, indent=2)
