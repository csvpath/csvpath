import unittest
import os
from csvpath.csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"
EMPTY = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}empty.csv"


class TestCsvPathFunctionsExists(unittest.TestCase):
    def test_function_exists1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                exists(#0)
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9

    def test_function_exists2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${EMPTY}[2]
            [
                exists(#0)
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 0
