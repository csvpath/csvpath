import os
import csv
from abc import ABC, abstractmethod
from .readers import UnmatchedReader
from csvpath.util.line_spooler import CsvLineSpooler, LineSpooler


class FileUnmatchedReader(UnmatchedReader):
    def __init__(self) -> None:
        super().__init__()
        self._unmatched: LineSpooler = None

    @property
    def unmatched(self) -> list[str]:
        if self._unmatched is None and self.result.instance_dir:
            self._unmatched = CsvLineSpooler(self.result)
            # if we don't set path in CsvLineSpooler it defaults to "unmatched.csv"
            p = os.path.join(self.result.instance_dir, "unmatched.csv")
            self._unmatched.path = p
        return self._unmatched
