import unittest
import os
from csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathFunctionsYes(unittest.TestCase):
    def test_function_yes(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*][
                yes()
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9
