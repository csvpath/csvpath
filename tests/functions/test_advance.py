import unittest
from csvpath.csvpath import CsvPath

PATH = "tests/test_resources/test.csv"


class TestFunctionsAdvance(unittest.TestCase):
    def test_function_advance1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1*]
            [
                push("cnt", count_lines())
                print("$.count_lines ")
                count.nocontrib() == 3 -> advance(2)
            ]"""
        )
        lines = path.collect()
        print(f"test_function_advance1: lines: {lines}")
        print(f"test_function_advance1: path vars: {path.variables}")
        assert len(lines) == 6
        assert path.variables["cnt"] == [1, 2, 3, 6, 7, 8]
