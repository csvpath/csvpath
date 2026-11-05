import unittest
import os
from csvpath.csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathFunctionsLineValuesStack(unittest.TestCase):
    def test_function_line_values_stack_1(self):
        path = CsvPath()
        path.parse(
            f""" ${PATH}[1] [
                    @stack = line_values_stack()
            ]"""
        )
        path.fast_forward()
        assert path.variables["stack"] == ["David", "Kermit", "hi!"]
