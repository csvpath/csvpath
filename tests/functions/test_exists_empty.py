import unittest
from csvpath.csvpath import CsvPath

PATH = "tests/test_resources/test.csv"
EMPTY = "tests/test_resources/empty.csv"


class TestFunctionsExistsAndEmpty(unittest.TestCase):
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
        print(f"\n test_function_exists1: lines: {lines}")
        print(f"test_function_exists1: path vars: {path.variables}")
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
        print(f"\n test_function_exists1: lines: {lines}")
        print(f"test_function_exists1: path vars: {path.variables}")
        assert len(lines) == 0

    def test_function_empty1(self):
        path = CsvPath()
        path.parse(
            f"""
            ${PATH}[*]
            [
                @d = has_dups()
                empty(@d)
            ]"""
        )
        lines = path.collect()
        print(f"\n test_function_exists1: lines: {lines}")
        print(f"test_function_exists1: path vars: {path.variables}")
        assert len(lines) == 9
