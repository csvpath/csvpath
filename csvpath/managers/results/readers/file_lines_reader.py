import os
import csv
from abc import ABC, abstractmethod
from .readers import LinesReader
from csvpath.util.line_spooler import LineSpooler, CsvLineSpooler
from typing import NewType


FileContent = NewType("FileContent", list[list[str]] | LineSpooler)


class FileLinesReader(LinesReader):
    def __init__(self) -> None:
        super().__init__()
        self._lines: LineSpooler = None

    @property
    def lines(self) -> FileContent:
        if self.result is None:
            raise Exception("Result cannot be None")
        if self._lines is None:
            self._lines = CsvLineSpooler(self.result)
        return self._lines
