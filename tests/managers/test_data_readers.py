import unittest
import pytest
from csvpath.managers.file_manager import FileManager
from csvpath.util.file_readers import (
    CsvDataFileReader,
    CsvDataReader,
    XlsxDataReader,
)

PATH_CSV = "tests/test_resources/test.csv"
PATH_XLSX = "tests/test_resources/test.xlsx"
PATH_XLSX2 = "tests/test_resources/test.xlsx#again"


class TestDataReaders(unittest.TestCase):
    def test_data_readers_1(self):
        print("")
        mgr = FileManager()
        mgr.add_named_file(name="csv", path=PATH_CSV)
        mgr.add_named_file(name="xlsx", path=PATH_XLSX)

        r1 = mgr.get_named_file_reader("csv")
        print(f"test: r1: {r1}")
        assert isinstance(r1, CsvDataReader)

        r2 = mgr.get_named_file_reader("xlsx")
        print(f"test: r2: {r2}")
        assert isinstance(r2, XlsxDataReader)

    def test_data_readers_2(self):
        print("")
        mgr = FileManager()
        mgr.add_named_file(name="csv", path=PATH_CSV)
        mgr.add_named_file(name="xlsx", path=PATH_XLSX)

        creader = mgr.get_named_file_reader("csv")
        print(f"test: reader: {creader}")
        assert isinstance(creader, CsvDataReader)

        xreader = mgr.get_named_file_reader("xlsx")
        print(f"test: xreader: {xreader}")
        assert isinstance(xreader, XlsxDataReader)
        xrow = None
        for i, xrow in enumerate(xreader.next()):
            for j, crow in enumerate(creader.next()):
                print(f"{i},{j} ({xrow}, {crow})")

                if crow == xrow:
                    break
            if i > j:
                print(f"no match for {xrow}")
        assert xrow is not None
        assert len(xrow) == 3
        assert xrow[0] == "Otter"

    def test_data_readers_3(self):
        print("")
        mgr = FileManager()
        mgr.add_named_file(name="xlsx", path=PATH_XLSX2)

        xreader = mgr.get_named_file_reader("xlsx")
        print(f"test: xreader: {xreader}")
        assert isinstance(xreader, XlsxDataReader)
        i = 0
        for i, xrow in enumerate(xreader.next()):
            if i == 17:
                assert xrow[0] == "100035"
        assert i == 17
