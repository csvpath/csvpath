import unittest
from csvpath.csvpath import CsvPath

PATH = "tests/test_resources/test.csv"


class TestFunctionsYes(unittest.TestCase):
    def test_function_yes(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                yes()
            ]"""
        )
        lines = path.collect()
        print(f"test_function_every: path vars: {path.variables}")
        print(f"lines: {lines}")
        assert len(lines) == 9
