import os
import unittest
from csvpath import CsvPath

UUIDS = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}uuid.csv"


class TestCsvPathFunctionsMetadata(unittest.TestCase):
    def test_function_metadata_1(self):
        path = CsvPath().parse(
            f"""~thought: hello world id:me~${UUIDS}[1*][
            @t = metadata( "thought" )
            @i = metadata( "id")
            @i == "me"
            push( "hello", @t )
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 3
        r = path.variables["hello"]
        assert r == ["hello world", "hello world", "hello world"]

    def test_function_metadata_2(self):
        path = CsvPath().parse(
            f"""~thought: hello world id:me~${UUIDS}[1*][
               metadata( "id") == "mex"
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 0

    def test_function_metadata_3(self):
        path = CsvPath().parse(
            f"""~thought: hello world id:me~${UUIDS}[1*][
               metadata( "notpresent") == "me"
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 0
