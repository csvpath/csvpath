import unittest
import os
from csvpath import CsvPath

PATH = f"tests{os.sep}test_resources{os.sep}test.csv"


class TestTotalLines(unittest.TestCase):
    def test_function_total_lines(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1]
            [ @total = total_lines() ]"""
        )
        lines = path.collect()
        assert len(lines) == 1
        assert path.variables["total"] == 9
