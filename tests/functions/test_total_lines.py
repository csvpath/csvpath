import unittest
from csvpath import CsvPath

PATH = "tests/test_resources/test.csv"


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
