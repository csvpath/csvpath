import unittest
from csvpath.csvpath import CsvPath

PATH = "tests/test_resources/test.csv"
EMPTY = "tests/test_resources/empty.csv"


class TestFunctionsExists(unittest.TestCase):
    def test_function_exists1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                exists(#0)
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9

    def test_function_exists2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${EMPTY}[2]
            [
                exists(#0)
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 0
