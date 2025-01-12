import subprocess
import os
from csvpath import CsvPaths


#
# this class is executed when a file arrives on a transfer set up
# by TransferCreator to handle inbound named-files.
#
class SftpPlusArrivalHandler:
    def __init__(self, path):
        self.csvpaths = CsvPaths()
        self._path = path
        self._named_file_name = None
        self._named_paths_name = None
        self._run_method = None

    @property
    def path(self) -> str:
        return self._path

    @property
    def run_method(self) -> str:
        return self.run_method

    @run_method.setter
    def run_method(self, n: str) -> None:
        self.run_method = n

    @property
    def named_file_name(self) -> str:
        return self._named_file_name

    @named_file_name.setter
    def named_file_name(self, n: str) -> None:
        self._named_file_name = n

    @property
    def named_paths_name(self) -> str:
        return self._named_paths_name

    @named_paths_name.setter
    def named_paths_name(self, n: str) -> None:
        self._named_paths_name = n

    def process_arrival(self) -> None:
        #
        # register the file
        #
        f = self.named_file_name
        self.csvpaths.file_manager.add_named_file(name=f, path=self.path)
        #
        # do the run
        #
        m = self.run_method
        p = self.named_paths_name
        if m is None or self.run_method == "collect_paths":
            self.csvpaths.collect_paths(filename=f, pathsname=p)
        elif m == "fast_forward_paths":
            self.csvpaths.fast_forward_paths(filename=f, pathsname=p)
        elif m == "collect_by_line":
            self.csvpaths.collect_by_line(filename=f, pathsname=p)
        elif m == "fast_forward_by_line":
            self.csvpaths.fast_forward_by_line(filename=f, pathsname=p)
        else:
            self.csvpaths.config.error("Run method is incorrect: {m}")
