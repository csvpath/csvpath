import unittest
import os
from csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathFunctionsUpperLower(unittest.TestCase):
    def test_function_upper_and_lower1(self):
        path = CsvPath()
        path.collect(
            f"""${PATH}[*][ @upper = upper(#firstname)
            @lower = lower(#firstname) ]"""
        )
        assert "upper" in path.variables
        assert "lower" in path.variables
        assert path.variables["lower"] == "frog"
        assert path.variables["upper"] == "FROG"

    def test_function_upper_and_lower2(self):
        lines = CsvPath().collect(
            f"""
            ${PATH}[*][
                    upper(#firstname)
                    lower(#firstname)
                ]"""
        )
        assert len(lines) == 9
