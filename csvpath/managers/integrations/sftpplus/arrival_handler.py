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
        self.csvpaths.logger.debug(
            "Handler: init: file_home: %s, named_file_name: %s",
            file_home,
            self.named_file_name,
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
        self.csvpaths.logger.debug(
            "Handler: process_arrival: name: %s, path: %s", f, self.path
        )
        self.csvpaths.file_manager.add_named_file(name=f, path=self.path)
        #
        # do work per sets of instructions found in the meta dir
        #
        p = self.path
        #
        # this is a file name. we need the path to it.
        #
        p = p[0 : p.rfind(os.sep)]
        #
        # add the meta dir name
        #
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
                self.csvpaths.logger.debug(
                    "Handler: process_arrival: found instructions at: %s", instructions
                )
                try:
                    with open(instructions, "r", encoding="utf-8") as file:
                        j = json.load(file)
                        self._process_meta_file(j)
                except Exception as e:
                    self.csvpaths.logger.error(e)
                    print(f"Error: {e}")
        else:
            self.csvpaths.logger.warning("No meta dir at %s. Creating it.", meta)
            os.makedirs(meta)

    def _process_meta_file(self, meta: dict) -> None:
        #
        # do a run
        #
        m = meta["method"]
        p = meta["named_paths_name"]
        archive = meta.get("archive")
        orig_archive = None
        if archive is not None:
            orig_archive = self.csvpath.config.get(section="results", name="archive")
            self.csvpath.config.add_to_config("results", "archive", archive)
        self.csvpaths.logger.debug(
            f"Handler: process_arrival: method: {m}, named_paths_name: {p}, archive: {archive}"
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
            self.csvpaths.config.error(
                "Handler: process_arrival: run method is incorrect: {m}"
            )
        if orig_archive is not None:
            self.csvpath.config.add_to_config("results", "archive", orig_archive)
