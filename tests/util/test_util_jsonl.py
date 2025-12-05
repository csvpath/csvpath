import unittest
import os
from datetime import datetime
from csvpath import CsvPath
from csvpath.matching.util.expression_utility import ExpressionUtility as exut
from csvpath.util.json.json_reader_helper import JsonReaderHelper
from csvpath.util.file_readers import DataFileReader

CSV_PATH = os.path.join("tests", "util", "test_resources", "test.csv")
JSONL_PATH = os.path.join("tests", "util", "test_resources", "test.jsonl")
JSONL_PATH_2 = os.path.join("tests", "util", "test_resources", "dates.jsonl")
JSONL_PATH_3 = os.path.join("tests", "util", "test_resources", "fish.jsonl")
JSONL_PATH_4 = os.path.join("tests", "util", "test_resources", "birds.jsonl")


class TestUtilJsonl(unittest.TestCase):
    def test_util_jsonl_1(self):
        csvlines = []
        with DataFileReader(CSV_PATH) as csv:
            for _ in csv.next():
                csvlines.append(_)
        with DataFileReader(JSONL_PATH) as json:
            for i, _ in enumerate(json.next()):
                assert _ == csvlines[i]
                print(f"json: {_}")
                print(f"csv: {csvlines[i]}\n")

    def test_util_jsonl_2(self):
        with DataFileReader(JSONL_PATH_2) as json:
            for i, _ in enumerate(json.next()):
                if i == 0:
                    assert _[0] == "date"
                else:
                    dt = exut.to_datetime(_[0])
                    print(f"json[{i}]: {_}: {dt}")
                    assert isinstance(dt, datetime)

    def test_util_jsonl_3(self):
        with DataFileReader(JSONL_PATH_3) as json:
            for i, _ in enumerate(json.next()):
                if i == 0:
                    assert _[0] == "fish"
                else:
                    assert _[0] in ["gold", "blue", "clown", "sea", "flat"]

    def test_util_jsonl_4(self):
        with DataFileReader(JSONL_PATH_4) as json:
            for i, _ in enumerate(json.next()):
                assert _[1] in ["jay", "bird", "bird", "gull", "hawk"]

    def test_util_jsonl_5(self):
        path = CsvPath()
        path.parse(
            f"""${JSONL_PATH_4}[*][
            row_table() in(#1 , "jay", "bird", "gull", "hawk")
        ]"""
        )
        lines = path.collect()
        assert len(lines) == 5
