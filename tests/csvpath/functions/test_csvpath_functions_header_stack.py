import unittest
import os
from csvpath.csvpath import CsvPath

PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathFunctionsHeadersStack(unittest.TestCase):
    def test_function_headers_stack_1(self):
        path = CsvPath()
        path.parse(
            f""" ${PATH}[3] [
                    @stack = headers_stack()
            ]"""
        )
        path.fast_forward()
        assert path.variables["stack"] == ["firstname", "lastname", "say"]
