import unittest
from csvpath import CsvPath

PATH = "tests/test_resources/test.csv"


class TestFunctionsYes(unittest.TestCase):
    def test_function_yes(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*][
                yes()
            ]"""
        )
        lines = path.collect()
        assert len(lines) == 9
