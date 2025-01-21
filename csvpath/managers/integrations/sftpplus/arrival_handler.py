import subprocess
import os
import json
from csvpath import CsvPaths


#
# this class is executed when a file arrives on a transfer set up
# by TransferCreator to handle inbound named-files.
#
class SftpPlusArrivalHandler:
    def __init__(self, path):
        self.csvpaths = CsvPaths()
        self._path = path
        file_home = path[0 : path.rfind(os.sep)]
        self.named_file_name = file_home[file_home.rfind(os.sep) + 1 :]
        print(
            f"Handler: init: file_home: {file_home}, named_file_name: {self.named_file_name}"
        )

    @property
    def path(self) -> str:
        return self._path

    @property
    def named_file_name(self) -> str:
        return self._named_file_name

    @named_file_name.setter
    def named_file_name(self, n: str) -> None:
        self._named_file_name = n

    def process_arrival(self) -> None:
        #
        # register the file
        #
        f = self.named_file_name
        print(f"Handler: process_arrival: name: {f}, path: {self.path}")
        self.csvpaths.file_manager.add_named_file(name=f, path=self.path)
        #
        # do work per set of instructions found in the meta dir
        #
        p = self.path
        p = p[0 : p.rfind(os.sep)]
        meta = os.path.join(p, "meta")
        #
        # loop on all files in meta. not expecting meta ever won't
        # exist. but it could be a possibility if we're only interested
        # in getting inbound files registered.
        #
        if os.path.exists(meta):
            ms = os.listdir(meta)
            for m in ms:
                instructions = os.path.join(meta, m)
                print(f"process_arrival: found instructions at: {instructions}")
                try:
                    with open(instructions, "r", encoding="utf-8") as file:
                        j = json.load(file)
                        self._process_meta_file(j)
                except Exception as e:
                    self.csvpaths.logger.error(e)
                    print(f"Error: {e}")

    def _process_meta_file(self, meta: dict) -> None:
        #
        # do a run
        #
        m = meta["method"]
        p = meta["named_paths_name"]
        archive = meta.get("archive")
        if archive is not None:
            self.csvpath.config.add_to_config(
                "results", "archive", archive, save_load=False
            )
        print(
            f"_process_meta_file: method: {m}, named_paths_name: {p}, archive: {archive}"
        )
        if m is None or m == "collect_paths":
            self.csvpaths.collect_paths(filename=self.named_file_name, pathsname=p)
        elif m == "fast_forward_paths":
            self.csvpaths.fast_forward_paths(filename=self.named_file_name, pathsname=p)
        elif m == "collect_by_line":
            self.csvpaths.collect_by_line(filename=self.named_file_name, pathsname=p)
        elif m == "fast_forward_by_line":
            self.csvpaths.fast_forward_by_line(
                filename=self.named_file_name, pathsname=p
            )
        else:
            self.csvpaths.config.error("Run method is incorrect: {m}")
