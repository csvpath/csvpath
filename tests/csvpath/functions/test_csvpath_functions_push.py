import unittest
import os
from csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathFunctionsPush(unittest.TestCase):
    def test_function_push_multi(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1]
            [
                push("a", 1, 23, 3, -2, 2)
            ]"""
        )
        path.fast_forward()
        assert "a" in path.variables
        assert path.variables.get("a") == [1, 23, 3, -2, 2]
