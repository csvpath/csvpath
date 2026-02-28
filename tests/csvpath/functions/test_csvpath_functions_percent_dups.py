import unittest
import os
from csvpath import CsvPath

NUMBERS = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}numbers.csv"
PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathFunctionsPercentDups(unittest.TestCase):
    def test_function_percent_dups1(self):
        path = CsvPath()
        path.parse(
            f""" ${PATH}[*] [
                @d = percent_dups()
            ]
            """
        )
        path.fast_forward()
        assert path.variables["d"] == 0

    def test_function_percent_dups2(self):
        path = CsvPath()
        path.parse(
            f""" ${PATH}[*] [
                @d = percent_dups(#lastname)
            ]
            """
        )
        path.fast_forward()
        assert path.variables["d"] > 66
