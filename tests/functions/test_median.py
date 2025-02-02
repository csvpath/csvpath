import unittest
import os
from csvpath.csvpath import CsvPath

PATH = f"tests{os.sep}test_resources{os.sep}test.csv"


class TestFunctionsMedian(unittest.TestCase):
    def test_function_median(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                @the_median = median(count(#lastname), "line")
                no()
            ]"""
        )
        lines = path.collect()
        assert path.variables["the_median"] == 3
        assert len(lines) == 0
