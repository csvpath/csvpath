import unittest
import os
from csvpath.csvpath import CsvPath

PATH = f"tests{os.sep}test_resources{os.sep}test.csv"


class TestFunctionsEnd(unittest.TestCase):
    def test_function_end1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                @end = end()
                no()
            ]"""
        )
        lines = path.collect()
        assert path.variables["end"] == "growl"
        assert len(lines) == 0

    def test_function_end2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                @end = end(2)
                no()
            ]"""
        )
        lines = path.collect()
        assert path.variables["end"] == "Frog"
        assert len(lines) == 0
