import unittest
from csvpath.csvpath import CsvPath

PATH = "tests/test_resources/test.csv"


class TestFunctionsCollect(unittest.TestCase):
    def test_function_collect1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1*]
            [
                collect(1)
                print("$.count_lines: $.line")
            ]"""
        )
        lines = path.collect()
        print(f"test_function_advance1: lines: {lines}")
        assert len(lines) == 8
        assert len(lines[0]) == 1

    def test_function_collect2(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[1*]
            [
                collect(0, "say")
                print("$.count_lines: $.line")
            ]"""
        )
        lines = path.collect()
        print(f"test_function_advance1: lines: {lines}")
        assert len(lines) == 8
        assert len(lines[0]) == 2
