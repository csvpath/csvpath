import unittest
import os
from csvpath.csvpath import CsvPath


PATH = f"tests{os.sep}csvpath{os.sep}test_resources{os.sep}test.csv"


class TestCsvPathFunctionsStrip(unittest.TestCase):
    def test_function_strip(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1]
            [
                @t = "  test  "
                @trimmable = @t
                @trimmed = strip(@trimmable)
            ]"""
        )
        path.fast_forward()
        assert path.variables["trimmable"] == "  test  "
        assert path.variables["trimmed"] == "test"
