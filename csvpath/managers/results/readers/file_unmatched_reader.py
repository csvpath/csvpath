import os
import csv
from abc import ABC, abstractmethod
from .readers import UnmatchedReader
from csvpath.util.line_spooler import CsvLineSpooler


class FileUnmatchedReader(UnmatchedReader):
    def __init__(self) -> None:
        super().__init__()
        self._unmatched = None

    @property
    def unmatched(self) -> list[str]:
        if self._unmatched is None and self.instance_dir:
            p = os.path.join(self.instance_dir, "unmatched.csv")
            self._unmatched = CsvLineSpooler(self.result)
            # if we don't set path it defaults to "data.csv"
            self._unmatched.path = p
        return self._unmatched
