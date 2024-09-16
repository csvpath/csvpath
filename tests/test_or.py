import unittest
from csvpath import CsvPath
from csvpath.scanning.scanner import Scanner
from csvpath.util.config import OnError

PATH = "tests/test_resources/test.csv"


class TestCsvPath(unittest.TestCase):
    def test_csvpath_logical_or1(self):
        path = CsvPath()
        path.AND = False
        path.parse(
            f"""${PATH}[*][
            #firstname == "Ants"
            #firstname == "Slug"
        ]"""
        )
        lines = path.collect()
        assert len(lines) == 2

    def test_csvpath_logical_or2(self):
        path = CsvPath()
        path.AND = False
        path.parse(
            f"""${PATH}[*][
            mod(count_lines(), 2) == 0
            mod(count_lines(), 3) == 0
        ]"""
        )
        lines = path.collect()
        assert len(lines) == 6
