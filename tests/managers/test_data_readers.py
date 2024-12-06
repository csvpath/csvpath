import unittest
import pytest
import os
import shutil
from csvpath.managers.files.file_manager import FileManager
from csvpath.util.file_readers import (
    CsvDataReader,
    XlsxDataReader,
)
from csvpath import CsvPaths

PATH_CSV = "tests/test_resources/test.csv"
PATH_XLSX = "tests/test_resources/test.xlsx"
PATH_XLSX2 = "tests/test_resources/test.xlsx#again"


class TestDataReaders(unittest.TestCase):
    def _clean(self) -> None:
        path = "inputs/named_files/xlsx"
        b = os.path.exists(path)
        if b:
            print("cleaning: path: {path}")
            shutil.rmtree(path)

    def test_data_readers_1(self):
        paths = CsvPaths()
        mgr = paths.file_manager
        mgr.add_named_file(name="csv", path=PATH_CSV)
        mgr.add_named_file(name="xlsx", path=PATH_XLSX)

        r1 = mgr.get_named_file_reader("csv")
        assert isinstance(r1, CsvDataReader)

        r2 = mgr.get_named_file_reader("xlsx")
        assert isinstance(r2, XlsxDataReader)

    def test_data_readers_2(self):
        self._clean()
        paths = CsvPaths()
        mgr = paths.file_manager
        mgr.add_named_file(name="csv", path=PATH_CSV)
        mgr.add_named_file(name="xlsx", path=PATH_XLSX)

        creader = mgr.get_named_file_reader("csv")
        assert isinstance(creader, CsvDataReader)
        xreader = mgr.get_named_file_reader("xlsx")
        assert isinstance(xreader, XlsxDataReader)
        xrow = None
        for i, xrow in enumerate(xreader.next()):
            for j, crow in enumerate(creader.next()):
                if crow == xrow:
                    break
        assert xrow is not None
        assert len(xrow) == 3
        assert xrow[0] == "Otter"

    def test_data_readers_3(self):
        self._clean()
        print("")
        paths = CsvPaths()
        mgr = paths.file_manager
        mgr.add_named_file(name="xlsx", path=PATH_XLSX2)

        xreader = mgr.get_named_file_reader("xlsx")
        assert isinstance(xreader, XlsxDataReader)
        i = 0
        for i, xrow in enumerate(xreader.next()):
            if i == 17:
                assert xrow[0] == "100035"
        assert i == 17
