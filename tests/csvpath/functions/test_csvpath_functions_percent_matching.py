import unittest
import os
from csvpath.csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathFunctionsPercentMatching(unittest.TestCase):
    def test_function_percent_matching_1(self):
        path = CsvPath()
        path.parse(
            f"""~validation-mode:print,no-raise~${PATH}[*][
                    #lastname == "Bat"
                    @p = percent_matching()
            ]"""
        )
        path.fast_forward()
        assert round(path.variables["p"], 2) == 66.67
